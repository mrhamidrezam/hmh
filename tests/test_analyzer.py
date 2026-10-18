from __future__ import annotations

import pytest

from hmh import analyze, analyze_many
from hmh.models import Report


def _project(tmp_path, files: dict) -> str:
    for relative, content in files.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return str(tmp_path)


PY = "import os\n\n# note\nprint(os)\nprint(1)\nprint(2)\n"
JS = "function f() {\n  // hi\n  return 1;\n}\n"


def test_totals_are_consistent(tmp_path):
    root = _project(tmp_path, {"a.py": PY, "b.js": JS})
    report = analyze(root)

    assert report.total_files == 2
    assert report.source_files == 2
    assert report.binary_files == 0
    assert report.code_lines + report.comment_lines + report.blank_lines == report.total_lines
    assert sum(s.code for s in report.languages) == report.code_lines
    assert sum(s.files for s in report.languages) == report.source_files


def test_language_detection_and_breakdown(tmp_path):
    root = _project(tmp_path, {"app.py": PY, "ui.js": JS, "README.md": "# hi\n\nbody\n"})
    report = analyze(root)
    names = {s.name for s in report.languages}
    assert names == {"Python", "JavaScript", "Markdown"}
    assert len(report.languages) == 3


def test_binary_file_is_weighed_not_counted(tmp_path):
    root = _project(tmp_path, {"a.py": PY})
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(64))
    report = analyze(root)

    assert report.binary_files == 1
    assert report.source_files == 1
    assert report.total_files == 2
    assert report.total_bytes > 0


def test_default_excludes_skip_dependency_dirs(tmp_path):
    _project(tmp_path, {"a.py": PY, "node_modules/pkg/index.js": JS,
                        ".venv/lib/site.py": PY, "__pycache__/x.py": PY})
    report = analyze(str(tmp_path))
    paths = [f.path for f in report.files]
    assert paths == ["a.py"]


def test_hidden_dirs_skipped_by_default_included_on_request(tmp_path):
    _project(tmp_path, {"a.py": PY, ".github/workflows/ci.yml": "on: push\n"})
    assert analyze(str(tmp_path)).total_files == 1
    assert analyze(str(tmp_path), include_hidden=True).total_files == 2


def test_gitignore_is_respected_and_can_be_disabled(tmp_path):
    _project(tmp_path, {"a.py": PY, "app.log": "line\n", ".gitignore": "*.log\n"})

    assert analyze(str(tmp_path)).total_files == 2  # a.py + .gitignore
    assert analyze(str(tmp_path), respect_gitignore=False).total_files == 3


def test_user_exclude_patterns(tmp_path):
    _project(tmp_path, {"keep.py": PY, "snapshot.snap": "x\n"})
    report = analyze(str(tmp_path), exclude=["*.snap"])
    paths = [f.path for f in report.files]
    assert "keep.py" in paths
    assert "snapshot.snap" not in paths


def test_single_file_analysis(tmp_path):
    target = tmp_path / "only.py"
    target.write_text(PY, encoding="utf-8")
    report = analyze(str(target))
    assert report.total_files == 1
    assert report.code_lines == 4


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze(str(tmp_path / "nope"))


def test_analyze_many_returns_one_report_per_path(tmp_path):
    first = _project(tmp_path / "a", {"x.py": PY})
    second = _project(tmp_path / "b", {"y.js": JS})
    reports = analyze_many([first, second])
    assert len(reports) == 2
    assert all(isinstance(r, Report) for r in reports)


def test_report_properties(tmp_path):
    root = _project(tmp_path, {"a.py": PY, "b.js": JS})
    report = analyze(root)

    assert report.languages_by_code[0].code >= report.languages_by_code[-1].code
    assert report.densest_files[0].code >= report.densest_files[-1].code
    assert report.size_human.endswith("B") or "K" in report.size_human or "M" in report.size_human
    assert report.duration >= 0
    assert report.top(1) == report.languages_by_code[:1]


def test_report_to_dict_shape(tmp_path):
    report = analyze(_project(tmp_path, {"a.py": PY}))
    payload = report.to_dict()
    assert payload["totals"]["code"] == report.code_lines
    assert payload["languages"][0]["name"] == "Python"
    assert isinstance(payload["files"], list)


def test_large_file_is_skipped_but_counted(tmp_path):
    root = _project(tmp_path, {"big.py": PY})
    (tmp_path / "huge.py").write_text("x = 1\n" * 50, encoding="utf-8")
    report = analyze(root, max_file_bytes=10)
    skipped = [f for f in report.files if f.path == "huge.py"][0]
    assert skipped.skipped == "too-large"
    assert skipped.lines == 0
    assert report.total_files == 2


def test_env_files_are_skipped(tmp_path):
    _project(tmp_path, {"a.py": PY, ".env": "SECRET=1\n"})
    report = analyze(str(tmp_path))
    assert ".env" not in [f.path for f in report.files]


def test_never_writes_anything(tmp_path):
    root = _project(tmp_path, {"a.py": PY, "sub/b.js": JS})
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    analyze(root)
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert before == after


def test_report_str_returns_table(tmp_path):
    report = analyze(_project(tmp_path, {"a.py": PY}))
    assert "hmh" in str(report)
    assert "Python" in str(report)
