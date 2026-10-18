from __future__ import annotations

import json

from hmh import __version__
from hmh.cli import main

PY = "import os\n\n# note\nprint(os)\nprint(1)\n"


def _project(tmp_path):
    (tmp_path / "app.py").write_text(PY, encoding="utf-8")
    (tmp_path / "style.css").write_text("body { color: red; }\n/* c */\n", encoding="utf-8")
    return str(tmp_path)


def test_default_table_output(tmp_path, capsys):
    assert main([_project(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "hmh" in out
    assert "Python" in out
    assert "style.css" not in out  # summary, not a file listing


def test_json_output(tmp_path, capsys):
    assert main([_project(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"]["files"] == 2


def test_markdown_output(tmp_path, capsys):
    assert main([_project(tmp_path), "--format", "markdown"]) == 0
    assert "| Language |" in capsys.readouterr().out


def test_files_flag_lists_paths(tmp_path, capsys):
    assert main([_project(tmp_path), "--files", "5"]) == 0
    assert "app.py" in capsys.readouterr().out


def test_top_flag(tmp_path, capsys):
    assert main([_project(tmp_path), "--top", "1"]) == 0
    out = capsys.readouterr().out
    assert "more languages" in out


def test_quiet_prints_nothing(tmp_path, capsys):
    assert main([_project(tmp_path), "--quiet"]) == 0
    assert capsys.readouterr().out == ""


def test_out_file(tmp_path, capsys):
    target = tmp_path / "report.md"
    assert main([_project(tmp_path), "--format", "markdown", "-o", str(target)]) == 0
    assert "| Language |" in target.read_text(encoding="utf-8")


def test_missing_path_returns_2(capsys):
    assert main(["/definitely/not/here"]) == 2
    assert "error:" in capsys.readouterr().err


def test_languages_flag(capsys):
    assert main(["--languages"]) == 0
    names = capsys.readouterr().out.splitlines()
    assert "Python" in names and "Rust" in names
    assert names == sorted(names)


def test_version_flag(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert __version__ in capsys.readouterr().out


def test_exclude_flag(tmp_path, capsys):
    root = _project(tmp_path)
    assert main([root, "--exclude", "*.css", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"]["files"] == 1


def test_no_gitignore_flag(tmp_path, capsys):
    (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(PY, encoding="utf-8")
    assert main([str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["files"] == 1

    assert main([str(tmp_path), "--no-gitignore", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["files"] == 2


def test_default_is_current_directory(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.py").write_text(PY, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0
    assert "Python" in capsys.readouterr().out
