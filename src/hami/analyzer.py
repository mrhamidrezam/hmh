"""The read-only walker that turns a directory into a :class:`Report`.

**hami never writes, moves or modifies anything it inspects.** Every file is
opened read-only, and binary blobs are only measured, never parsed.
"""

from __future__ import annotations

import fnmatch
import os
import time
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .gitignore import GitIgnore
from .languages import (
    BINARY_EXTENSIONS,
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_PATTERNS,
    count_lines,
    detect,
)
from .models import FileStat, LanguageStats, Report

PathLike = Union[str, Path]

#: Files never worth counting, wherever they live.
IGNORED_FILES = frozenset({".ds_store", "thumbs.db", "desktop.ini"})

#: How many leading bytes are sniffed for a NUL byte.
_SNIFF_BYTES = 8192


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def _excluded_dir(name: str) -> bool:
    if name.lower() in DEFAULT_EXCLUDE_DIRS:
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in DEFAULT_EXCLUDE_PATTERNS)


def _read_text(path: str, size: int, max_file_bytes: int) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(text, skip_reason)``. ``text is None`` means the file was skipped."""
    if max_file_bytes > 0 and size > max_file_bytes:
        return None, "too-large"
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return None, f"unreadable:{type(exc).__name__}"
    if b"\x00" in raw[:_SNIFF_BYTES]:
        return None, "binary-content"
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), None
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), None  # pragma: no cover


def _iter_files(
    root: Path,
    *,
    include_hidden: bool,
    gitignore: GitIgnore,
    follow_symlinks: bool,
) -> Iterator[Tuple[str, str]]:
    """Yield ``(abspath, relative_posix)`` for every file worth measuring."""
    stack = [str(root)]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            name = entry.name
            if name.lower() in IGNORED_FILES:
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=follow_symlinks)
            except OSError:
                continue
            relative = os.path.relpath(entry.path, root).replace(os.sep, "/")

            if is_dir:
                if not include_hidden and _is_hidden(name):
                    continue
                if _excluded_dir(name):
                    continue
                if gitignore.matches(relative):
                    continue
                stack.append(entry.path)
                continue

            # Dotfiles are meaningful (``.gitignore``, ``.editorconfig``) and are
            # always counted; environment secrets are not.
            if name.lower().startswith(".env"):
                continue
            if gitignore.matches(relative):
                continue
            yield entry.path, relative


def analyze(
    path: PathLike = ".",
    *,
    include_hidden: bool = False,
    exclude: Sequence[str] = (),
    respect_gitignore: bool = True,
    follow_symlinks: bool = False,
    max_file_bytes: int = 20_000_000,
    extra_ignores: Sequence[str] = (),
) -> Report:
    """Analyse a project directory (or a single file) and return a :class:`Report`.

    Parameters
    ----------
    path:
        Directory to walk, or a single file to measure.
    include_hidden:
        Also walk dot-directories such as ``.github`` or ``.venv``.
    exclude:
        Extra gitignore-style patterns to skip, e.g. ``("tests/*.snap",)``.
    respect_gitignore:
        Honour the project's ``.gitignore`` (on by default).
    follow_symlinks:
        Traverse symbolic links instead of skipping them.
    max_file_bytes:
        Files larger than this are counted but not line-scanned.
    extra_ignores:
        More directory names to skip, merged with the built-in defaults.
    """
    started = time.perf_counter()
    root = Path(path).expanduser()

    if root.is_file():
        return _analyze_single_file(root)

    if not root.exists():
        raise FileNotFoundError(f"no such path: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    root = root.resolve()

    gitignore = GitIgnore.from_root(root) if respect_gitignore else GitIgnore.empty()
    if exclude:
        gitignore.extend(exclude)
    if extra_ignores:
        gitignore.extend(extra_ignores)

    files: List[FileStat] = []
    for abspath, relative in _iter_files(
        root,
        include_hidden=include_hidden,
        gitignore=gitignore,
        follow_symlinks=follow_symlinks,
    ):
        files.append(_measure(abspath, relative, max_file_bytes))

    files.sort(key=lambda item: item.path)
    report = _summarize(str(root), files)
    report.duration = time.perf_counter() - started
    return report


def _analyze_single_file(path: Path) -> Report:
    stat = path.stat()
    files = [_measure(str(path), path.name, 0, forced_size=stat.st_size)]
    report = _summarize(str(path.parent), files)
    report.duration = 0.0
    return report


def _measure(abspath: str, relative: str, max_file_bytes: int,
             forced_size: Optional[int] = None) -> FileStat:
    try:
        size = forced_size if forced_size is not None else os.path.getsize(abspath)
    except OSError:
        return FileStat(path=relative, language=None, size=0,
                        is_binary=False, skipped="stat-failed")

    suffix = Path(relative).suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return FileStat(path=relative, language=None, size=size, is_binary=True)

    try:
        with open(abspath, "rb") as handle:
            head = handle.read(256)
    except OSError:
        head = b""

    language = detect(relative, head)
    text, reason = _read_text(abspath, size, max_file_bytes)

    if text is None:
        return FileStat(
            path=relative,
            language=language,
            size=size,
            is_binary=(reason == "binary-content"),
            skipped=reason,
        )

    code, comments, blank = count_lines(text, language)
    total = code + comments + blank
    return FileStat(
        path=relative,
        language=language,
        size=size,
        lines=total,
        code=code,
        comments=comments,
        blank=blank,
    )


def _summarize(root: str, files: List[FileStat]) -> Report:
    report = Report(root=root, files=files)
    report.total_files = len(files)

    per_language: Dict[str, LanguageStats] = {}
    for item in files:
        report.total_bytes += item.size
        if item.is_binary:
            report.binary_files += 1
            continue
        if item.language is None:
            continue

        report.source_files += 1
        report.source_bytes += item.size
        report.total_lines += item.lines
        report.code_lines += item.code
        report.comment_lines += item.comments
        report.blank_lines += item.blank

        stats = per_language.get(item.language)
        if stats is None:
            stats = per_language[item.language] = LanguageStats(name=item.language)
        stats.files += 1
        stats.bytes += item.size
        stats.lines += item.lines
        stats.code += item.code
        stats.comments += item.comments
        stats.blank += item.blank

    report.languages = sorted(per_language.values(), key=lambda s: (-s.code, s.name))
    return report


def analyze_many(paths: Iterable[PathLike], **options: object) -> List[Report]:
    """Analyse several projects and return one :class:`Report` per path."""
    return [analyze(entry, **options) for entry in paths]  # type: ignore[arg-type]
