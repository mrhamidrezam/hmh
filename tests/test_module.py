from __future__ import annotations

import subprocess
import sys

from hmh.cli import main


def test_module_execution_prints_help(capsys):
    result = subprocess.run(
        [sys.executable, "-m", "hmh", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "hmh" in result.stdout


def test_module_execution_analyses_a_path(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "hmh", str(tmp_path), "--format", "json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert '"code"' in result.stdout


def test_cli_main_is_importable():
    assert callable(main)
