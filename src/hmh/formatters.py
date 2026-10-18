"""Render a :class:`~hmh.models.Report` as text, JSON, CSV or Markdown."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Optional, Sequence

from .models import LanguageStats, Report

FORMATS = ("table", "json", "csv", "markdown")


def _number(value: int) -> str:
    return f"{value:,}"


def _columns(headers: Sequence[str], rows: Sequence[Sequence[str]],
             right_from: int = 1) -> str:
    """Left-align the first ``right_from`` columns, right-align the rest."""
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells: Sequence[str]) -> str:
        rendered = []
        for index, cell in enumerate(cells):
            rendered.append(
                cell.ljust(widths[index]) if index < right_from
                else cell.rjust(widths[index])
            )
        return "  ".join(rendered).rstrip()

    out = [line(headers), "  ".join("-" * width for width in widths)]
    out.extend(line(row) for row in rows)
    return "\n".join(out)


def _language_rows(report: Report, top: Optional[int],
                   sort: str) -> List[LanguageStats]:
    languages = report.languages
    if sort == "bytes":
        languages = report.languages_by_bytes
    elif sort == "lines":
        languages = sorted(languages, key=lambda s: (-s.lines, s.name))
    elif sort == "files":
        languages = sorted(languages, key=lambda s: (-s.files, s.name))
    elif sort == "name":
        languages = sorted(languages, key=lambda s: s.name)
    else:
        languages = report.languages_by_code
    return languages[:top] if top else languages


def _file_rows(report: Report, top: int) -> List[List[str]]:
    return [
        [item.path, item.language or ("binary" if item.is_binary else "unknown"),
         _number(item.code), item.size_human]
        for item in report.densest_files[:top]
    ]


def format_table(report: Report, *, top: Optional[int] = None, sort: str = "code",
                 show_files: int = 0) -> str:
    languages = _language_rows(report, top, sort)
    lines: List[str] = []

    lines.append("hmh  ·  read-only project analysis")
    lines.append(f"path      {report.root}")
    lines.append(
        f"scanned   {_number(report.total_files)} files "
        f"({_number(report.source_files)} source · {_number(report.binary_files)} binary)"
        + (f" · {report.excluded_dirs} excluded" if report.excluded_dirs else "")
    )
    lines.append(f"size      {report.size_human}")
    lines.append(
        f"lines     {_number(report.total_lines)}  "
        f"=  code {_number(report.code_lines)}  ·  "
        f"comments {_number(report.comment_lines)}  ·  "
        f"blank {_number(report.blank_lines)}"
    )
    lines.append(f"comments  {report.comments_per_code} per code line")
    lines.append(f"duration  {report.duration * 1000:.0f} ms")

    if languages:
        lines.append("")
        headers = ("LANGUAGE", "FILES", "CODE", "COMMENTS", "BLANK", "SHARE")
        rows = [
            [
                stats.name,
                _number(stats.files),
                _number(stats.code),
                _number(stats.comments),
                _number(stats.blank),
                f"{stats.share_of(report.code_lines):.1f}%",
            ]
            for stats in languages
        ]
        lines.append(_columns(headers, rows, right_from=1))
        if top and len(report.languages) > len(languages):
            lines.append(
                f"... and {len(report.languages) - len(languages)} more languages"
            )

    if show_files:
        files = _file_rows(report, show_files)
        if files:
            lines.append("")
            lines.append(f"Largest source files (by code lines)")
            lines.append(
                _columns(("FILE", "LANGUAGE", "CODE", "SIZE"), files, right_from=2)
            )

    return "\n".join(lines)


def format_markdown(report: Report, *, top: Optional[int] = None,
                    sort: str = "code") -> str:
    languages = _language_rows(report, top, sort)
    out: List[str] = []
    out.append(f"### Project analysis — `{report.root}`")
    out.append("")
    out.append(
        f"> {_number(report.total_files)} files · {report.size_human} · "
        f"**{_number(report.code_lines)}** code lines · "
        f"{_number(report.comment_lines)} comments · "
        f"{_number(report.blank_lines)} blank · "
        f"{report.duration * 1000:.0f} ms"
    )
    out.append("")
    if languages:
        out.append("| Language | Files | Code | Comments | Blank | Share |")
        out.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for stats in languages:
            out.append(
                f"| {stats.name} | {stats.files} | {_number(stats.code)} | "
                f"{_number(stats.comments)} | {_number(stats.blank)} | "
                f"{stats.share_of(report.code_lines):.1f}% |"
            )
        out.append("")
    out.append("_Generated by [hmh](https://pypi.org/project/hmh/) — read-only._")
    return "\n".join(out)


def format_csv(report: Report, *, top: Optional[int] = None,
               sort: str = "code") -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        ["language", "files", "bytes", "lines", "code", "comments", "blank", "share_percent"]
    )
    for stats in _language_rows(report, top, sort):
        writer.writerow([
            stats.name, stats.files, stats.bytes, stats.lines,
            stats.code, stats.comments, stats.blank,
            stats.share_of(report.code_lines),
        ])
    return buffer.getvalue()


def format_json(report: Report, *, top: Optional[int] = None, sort: str = "code",
                show_files: int = 0) -> str:
    payload = report.to_dict()
    payload["languages"] = [s.to_dict() for s in _language_rows(report, top, sort)]
    if show_files:
        payload["largest_files"] = [f.to_dict() for f in report.densest_files[:show_files]]
    else:
        payload.pop("files", None)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def format_report(
    report: Report,
    fmt: str = "table",
    *,
    top: Optional[int] = None,
    sort: str = "code",
    show_files: int = 0,
) -> str:
    """Render ``report`` in one of :data:`FORMATS`."""
    if fmt == "json":
        return format_json(report, top=top, sort=sort, show_files=show_files)
    if fmt == "csv":
        return format_csv(report, top=top, sort=sort)
    if fmt == "markdown":
        return format_markdown(report, top=top, sort=sort)
    return format_table(report, top=top, sort=sort, show_files=show_files)
