"""hami — a read-only project analyzer.

Point it at any folder and get back a full picture of what is inside: how many
lines, in how many languages, how big everything is — **without a single byte
ever being written, moved or modified**.

::

    import hami

    report = hami.analyze("~/projects/myapp")
    print(f"{report.code_lines} code lines across {len(report.languages)} languages")

    for lang in report.top(5):
        print(f"{lang.name:<15} {lang.code:>7,}")
"""

from __future__ import annotations

from .analyzer import analyze, analyze_many
from .formatters import format_report
from .gitignore import GitIgnore
from .languages import known_languages
from .models import FileStat, LanguageStats, Report

__version__ = "0.1.0"

__all__ = [
    "FileStat",
    "GitIgnore",
    "LanguageStats",
    "Report",
    "__version__",
    "analyze",
    "analyze_many",
    "format_report",
    "known_languages",
]
