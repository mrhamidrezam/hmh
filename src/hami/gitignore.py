"""A small, dependency-free subset of ``.gitignore`` matching.

Supported: comments, blank lines, ``*``, ``**``, ``?``, anchoring with a
leading ``/``, directory-only rules with a trailing ``/``, matching at any
depth, and ``!`` negation (last rule wins).

Intentionally out of scope: character classes (``[a-z]``), escaped hashes and
``.git/info/exclude``. A directory-only rule also matches a file of the same
name — a rare, harmless deviation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Pattern, Sequence, Tuple

__all__ = ["GitIgnore", "compile_pattern"]

Rule = Tuple[Pattern[str], bool]  # (regex, negated)


def _translate(fragment: str) -> str:
    """Translate one gitignore glob fragment into a regular expression."""
    out: List[str] = []
    index, length = 0, len(fragment)
    while index < length:
        char = fragment[index]
        if char == "*":
            if fragment.startswith("**/", index):
                out.append(r"(?:[^/]+/)*")   # zero or more directories
                index += 3
                continue
            if fragment.startswith("**", index):
                out.append(r".*")
                index += 2
                continue
            out.append(r"[^/]*")             # never crosses a separator
            index += 1
        elif char == "?":
            out.append(r"[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    return "".join(out)


def compile_pattern(
    raw: str, *, negate: bool, anchored: bool, dir_only: bool
) -> Optional[Rule]:
    """Compile one gitignore line into ``(regex, negated)``, or ``None``."""
    body = raw
    if dir_only and body.endswith("/"):
        body = body[:-1]
    # any separator other than a trailing one anchors the rule to the root
    if "/" in body:
        anchored = True
    if body.startswith("/"):
        body = body[1:]
        anchored = True
    if not body:
        return None

    core = _translate(body)
    prefix = "^" if anchored else r"^(?:.*/)?"
    try:
        return re.compile(f"{prefix}{core}(?:/.*)?$"), negate
    except re.error:  # pragma: no cover - defensive
        return None


class GitIgnore:
    """Matchers gathered from one or more ``.gitignore`` files."""

    def __init__(self, rules: Sequence[Rule] = ()) -> None:
        self._rules = list(rules)

    @classmethod
    def empty(cls) -> "GitIgnore":
        return cls()

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> "GitIgnore":
        rules: List[Rule] = []
        for line in lines:
            text = line.rstrip("\r\n")
            if not text.strip() or text.lstrip().startswith("#"):
                continue
            negated = text.startswith("!")
            if negated:
                text = text[1:]
            text = text.strip()
            if not text:
                continue
            compiled = compile_pattern(
                text, negate=negated, anchored=False, dir_only=text.endswith("/")
            )
            if compiled:
                rules.append(compiled)
        return cls(rules)

    @classmethod
    def from_root(cls, root: Path) -> "GitIgnore":
        """Read ``root/.gitignore`` if present, otherwise return an empty set."""
        try:
            text = (Path(root) / ".gitignore").read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return cls.empty()
        return cls.from_lines(text.splitlines())

    @property
    def rules(self) -> List[Rule]:
        return list(self._rules)

    def extend(self, lines: Iterable[str]) -> "GitIgnore":
        """Append more rules; later rules take precedence when they match."""
        self._rules.extend(GitIgnore.from_lines(lines)._rules)
        return self

    def matches(self, relative_path: str) -> bool:
        """Whether ``relative_path`` (posix style) should be excluded."""
        path = relative_path.replace("\\", "/").strip("/")
        if not path:
            return False
        excluded = False
        for regex, negated in self._rules:
            if regex.match(path):
                excluded = not negated
        return excluded

    def __len__(self) -> int:
        return len(self._rules)

    def __bool__(self) -> bool:
        return bool(self._rules)
