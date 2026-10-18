from __future__ import annotations

from hami.gitignore import GitIgnore, compile_pattern


def test_simple_name_matches_at_any_depth():
    rules = GitIgnore.from_lines(["node_modules"])
    assert rules.matches("node_modules")
    assert rules.matches("packages/app/node_modules")
    assert not rules.matches("src/app.py")


def test_trailing_slash_matches_directory_contents():
    rules = GitIgnore.from_lines(["dist/"])
    assert rules.matches("dist")
    assert rules.matches("dist/assets/app.js")
    assert not rules.matches("src/dist.py")


def test_anchored_pattern_does_not_match_nested():
    rules = GitIgnore.from_lines(["/build"])
    assert rules.matches("build")
    assert not rules.matches("src/build")


def test_star_does_not_cross_directories():
    rules = GitIgnore.from_lines(["*.log"])
    assert rules.matches("app.log")
    assert rules.matches("logs/deep/app.log")
    assert not rules.matches("logs/deep/app.log.txt")


def test_double_star_crosses_directories():
    rules = GitIgnore.from_lines(["a/**/b"])
    assert rules.matches("a/b")
    assert rules.matches("a/x/y/b")
    assert not rules.matches("z/a/b")


def test_negation_keeps_file():
    rules = GitIgnore.from_lines(["*.log", "!keep.log"])
    assert rules.matches("app.log")
    assert not rules.matches("keep.log")


def test_last_rule_wins():
    rules = GitIgnore.from_lines(["!keep.log", "*.log"])
    assert rules.matches("keep.log")


def test_comments_and_blank_lines_ignored():
    rules = GitIgnore.from_lines(["", "   ", "# a comment", "*.py"])
    assert len(rules) == 1
    assert rules.matches("main.py")


def test_question_mark_matches_single_character():
    rules = GitIgnore.from_lines(["file?.txt"])
    assert rules.matches("file1.txt")
    assert not rules.matches("file12.txt")


def test_empty_and_empty_path():
    assert not GitIgnore.empty().matches("anything")
    assert not GitIgnore.from_lines(["*.py"]).matches("")


def test_extend_adds_rules():
    rules = GitIgnore.from_lines(["*.log"])
    rules.extend(["*.tmp"])
    assert rules.matches("a.log") and rules.matches("a.tmp")


def test_compile_pattern_rejects_useless_line():
    assert compile_pattern("/", negate=False, anchored=False, dir_only=True) is None


def test_from_root_missing_file_is_empty(tmp_path):
    assert len(GitIgnore.from_root(tmp_path)) == 0


def test_from_root_reads_file(tmp_path):
    (tmp_path / ".gitignore").write_text("*.log\n!important.log\n", encoding="utf-8")
    rules = GitIgnore.from_root(tmp_path)
    assert rules.matches("run.log")
    assert not rules.matches("important.log")
