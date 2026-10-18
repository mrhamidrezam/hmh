from __future__ import annotations

from hami.languages import LANGUAGES, count_lines, detect, known_languages


def test_detect_by_extension():
    assert detect("src/app.py") == "Python"
    assert detect("src/app.tsx") == "TypeScript"
    assert detect("styles/main.css") == "CSS"
    assert detect("docs/README.md") == "Markdown"
    assert detect("Dockerfile") == "Dockerfile"
    assert detect("Makefile") == "Makefile"
    assert detect("CMakeLists.txt") == "CMake"


def test_detect_is_case_insensitive():
    assert detect("src/App.PY") == "Python"
    assert detect("MAKEFILE") == "Makefile"


def test_detect_unknown_returns_none():
    assert detect("data/nothing.xyz") is None


def test_detect_shebang_without_extension():
    assert detect("bin/tool", b"#!/usr/bin/env python3\n") == "Python"
    assert detect("bin/tool", b"#!/bin/bash\n") == "Shell"
    assert detect("bin/tool", b"#!/usr/bin/env node\n") == "JavaScript"
    assert detect("bin/tool", b"#!/usr/bin/perl\n") == "Perl"


def test_known_languages_sorted_and_non_empty():
    names = known_languages()
    assert len(names) >= 50
    assert list(names) == sorted(names)
    assert "Python" in names and "Rust" in names


def test_every_language_has_a_name():
    assert all(lang.name for lang in LANGUAGES.values())


# -- counting -------------------------------------------------------------
def test_python_counts_code_comments_blank():
    text = '"""doc."""\nimport os\n\n# a comment\nprint(os)\n'
    code, comments, blank = count_lines(text, "Python")
    assert (code, comments, blank) == (3, 1, 1)


def test_python_hash_inside_string_is_not_a_comment():
    text = 'url = "http://x/#frag"\n'
    code, comments, blank = count_lines(text, "Python")
    assert (code, comments, blank) == (1, 0, 0)


def test_multiline_string_is_code_not_comment():
    text = 'x = """\nstill string\n"""\n'
    code, comments, blank = count_lines(text, "Python")
    assert comments == 0
    assert code == 3


def test_c_style_line_and_block_comments():
    text = "int x; // trailing\n/* block\n   still block */\nint y;\n"
    code, comments, blank = count_lines(text, "C")
    assert code == 2
    assert comments == 2
    assert blank == 0


def test_block_comment_opening_and_code_after():
    text = "/* c */ int x;\n"
    code, comments, blank = count_lines(text, "C")
    assert (code, comments) == (1, 0)


def test_line_comment_after_code_counts_as_code():
    text = "int x; // note\n"
    code, comments, blank = count_lines(text, "C")
    assert (code, comments) == (1, 0)


def test_html_block_comments():
    text = "<div></div>\n<!-- note -->\n\n<p></p>\n"
    code, comments, blank = count_lines(text, "HTML")
    assert (code, comments, blank) == (2, 1, 1)


def test_language_without_comment_rules():
    text = "a,b\n\n1,2\n"
    code, comments, blank = count_lines(text, "CSV")
    assert (code, comments, blank) == (2, 0, 1)


def test_unknown_language_counts_non_blank_as_code():
    text = "hello\n\nworld\n"
    code, comments, blank = count_lines(text, None)
    assert (code, comments, blank) == (2, 0, 1)


def test_blank_lines_with_whitespace_only():
    text = "   \n\t\nx\n"
    code, comments, blank = count_lines(text, "Python")
    assert (code, blank) == (1, 2)


def test_escaped_quote_does_not_end_string():
    text = 's = "he said \\"hi\\" # not a comment"\n'
    code, comments, _ = count_lines(text, "Python")
    assert (code, comments) == (1, 0)


def test_empty_text():
    assert count_lines("", "Python") == (0, 0, 0)
