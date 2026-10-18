"""Data structures produced by hmh."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _human_size(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@dataclass(frozen=True)
class FileStat:
    """What hmh learned about a single file. Never written back."""

    path: str
    language: Optional[str]
    size: int
    lines: int = 0
    code: int = 0
    comments: int = 0
    blank: int = 0
    is_binary: bool = False
    skipped: Optional[str] = None

    @property
    def is_source(self) -> bool:
        return not self.is_binary and self.language is not None

    @property
    def size_human(self) -> str:
        return _human_size(self.size)

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "size": self.size,
            "lines": self.lines,
            "code": self.code,
            "comments": self.comments,
            "blank": self.blank,
            "binary": self.is_binary,
            "skipped": self.skipped,
        }


@dataclass
class LanguageStats:
    """Aggregated numbers for one language across the whole project."""

    name: str
    files: int = 0
    bytes: int = 0
    lines: int = 0
    code: int = 0
    comments: int = 0
    blank: int = 0

    @property
    def code_per_file(self) -> float:
        """Average code lines per file — a rough density signal."""
        return round(self.code / self.files, 1) if self.files else 0.0

    def share_of(self, total_code: int) -> float:
        """Percentage of all counted code lines this language owns."""
        return round(100.0 * self.code / total_code, 1) if total_code else 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "files": self.files,
            "bytes": self.bytes,
            "lines": self.lines,
            "code": self.code,
            "comments": self.comments,
            "blank": self.blank,
        }


@dataclass
class Report:
    """Everything hmh found, ready to print, export or inspect."""

    root: str
    files: List[FileStat] = field(default_factory=list)
    languages: List[LanguageStats] = field(default_factory=list)
    total_files: int = 0
    source_files: int = 0
    binary_files: int = 0
    total_bytes: int = 0
    source_bytes: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    excluded_dirs: int = 0
    duration: float = 0.0

    # -- convenience --------------------------------------------------
    @property
    def languages_by_code(self) -> List[LanguageStats]:
        return sorted(self.languages, key=lambda s: (-s.code, s.name))

    @property
    def languages_by_bytes(self) -> List[LanguageStats]:
        return sorted(self.languages, key=lambda s: (-s.bytes, s.name))

    @property
    def largest_files(self) -> List[FileStat]:
        return sorted(self.files, key=lambda f: (-f.size, f.path))

    @property
    def densest_files(self) -> List[FileStat]:
        return sorted(
            (f for f in self.files if f.is_source),
            key=lambda f: (-f.code, f.path),
        )

    @property
    def size_human(self) -> str:
        return _human_size(self.total_bytes)

    @property
    def comments_per_code(self) -> float:
        return round(self.comment_lines / self.code_lines, 3) if self.code_lines else 0.0

    def top(self, n: int) -> List[LanguageStats]:
        """The ``n`` languages with the most code lines."""
        return self.languages_by_code[: max(0, n)]

    def to_dict(self) -> Dict[str, object]:
        return {
            "root": self.root,
            "totals": {
                "files": self.total_files,
                "source_files": self.source_files,
                "binary_files": self.binary_files,
                "bytes": self.total_bytes,
                "source_bytes": self.source_bytes,
                "lines": self.total_lines,
                "code": self.code_lines,
                "comments": self.comment_lines,
                "blank": self.blank_lines,
                "excluded_dirs": self.excluded_dirs,
            },
            "duration": round(self.duration, 4),
            "languages": [stats.to_dict() for stats in self.languages_by_code],
            "files": [item.to_dict() for item in self.files],
        }

    def __str__(self) -> str:  # pragma: no cover - formatting is tested
        from .formatters import format_report

        return format_report(self, "table")
