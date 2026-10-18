from __future__ import annotations

import json

import pytest

from hmh import analyze, format_report
from hmh.formatters import FORMATS, format_csv, format_json, format_markdown, format_table

PY = "import os\n\n# note\nprint(os)\nprint(1)\nprint(2)\n"
JS = "function f() {\n  // hi\n  return 1;\n}\n"


@pytest.fixture()
def report(tmp_path):
    (tmp_path / "a.py").write_text(PY, encoding="utf-8")
    (tmp_path / "b.js").write_text(JS, encoding="utf-8")
    return analyze(str(tmp_path))


def test_table_contains_summary_and_languages(report):
    text = format_report(report, "table")
    assert "read-only project analysis" in text
    assert "Python" in text and "JavaScript" in text
    assert "lines" in text and "code" in text
    assert report.duration >= 0


def test_table_top_limits_languages(report):
    text = format_table(report, top=1)
    assert text.count("JavaScript") + text.count("Python") == 1
    assert "more languages" in text


def test_table_show_files(report):
    text = format_table(report, show_files=3)
    assert "Largest source files" in text
    assert "a.py" in text


def test_json_is_valid_and_has_totals(report):
    payload = json.loads(format_json(report))
    assert payload["totals"]["code"] == report.code_lines
    assert len(payload["languages"]) == 2
    assert "files" not in payload  # hidden unless show_files


def test_json_includes_files_when_requested(report):
    payload = json.loads(format_json(report, show_files=2))
    assert len(payload["largest_files"]) == 2


def test_csv_shape(report):
    text = format_csv(report)
    rows = [line for line in text.strip().splitlines()]
    assert rows[0].startswith("language,files,bytes,lines,code")
    assert len(rows) == 3  # header + 2 languages


def test_markdown_is_a_table(report):
    text = format_markdown(report)
    assert text.startswith("### Project analysis")
    assert "| Language | Files | Code |" in text
    assert "| Python |" in text
    assert "[hmh]" in text


def test_all_formats_supported(report):
    for fmt in FORMATS:
        assert format_report(report, fmt).strip()


def test_sort_variants(report):
    for sort in ("code", "lines", "files", "bytes", "name"):
        assert format_table(report, sort=sort).strip()


def test_share_percentages_sum_roughly_to_100(report):
    shares = [s.share_of(report.code_lines) for s in report.languages]
    assert abs(sum(shares) - 100.0) < 0.5


def test_empty_project_formats(tmp_path):
    report = analyze(str(tmp_path))
    for fmt in FORMATS:
        assert format_report(report, fmt).strip()
