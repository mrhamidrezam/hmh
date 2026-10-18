<p align="center">
  <img src="https://raw.githubusercontent.com/mrhamidrezam/hmh/main/assets/banner.svg" alt="hmh — read-only project analyzer" width="100%" />
</p>

<p align="center">
  <strong>Split any project into its spectrum.</strong><br/>
  Lines of code, languages, sizes and structure — <em>without ever touching your files</em>.
</p>

<p align="center">
  <a href="https://pypi.org/project/hmh/"><img alt="PyPI" src="https://img.shields.io/pypi/v/hmh?color=4c1&label=PyPI"></a>
  <a href="https://pypi.org/project/hmh/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/hmh"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <a href="https://github.com/mrhamidrezam/hmh/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/mrhamidrezam/hmh/actions/workflows/ci.yml/badge.svg"></a>
</p>

---

`hmh` is a **read-only project analyzer** for Python. Point it at any folder and it tells you
exactly what is inside: how many lines, in how many languages, how big everything is, and which
files carry the most weight.

It reads. It never writes.

```bash
pip install hmh
hmh .
```

```text
hmh  ·  read-only project analysis
path      /home/you/projects/myapp
scanned   412 files (388 source · 24 binary)
size      5.4 MB
lines     71,338  =  code 54,120  ·  comments 9,004  ·  blank 8,214
comments  0.166 per code line
duration  312 ms

LANGUAGE              FILES        CODE   COMMENTS      BLANK   SHARE
Python                  142     28,410      5,201      4,118   52.5%
TypeScript               96     14,902      2,140      2,310   27.5%
JavaScript               71      6,744      1,003      1,020   12.5%
CSS                      34      2,860        412        488    5.3%
YAML                     22        680        188        144    1.3%
Markdown                 23          42         60         34    0.1%
```

## Why `hmh`?

Most code counters are useful but invasive — they beg you to add config, install a daemon, or
grant write access. `hmh` has exactly one hard rule:

> **`hmh` NEVER modifies the source project.**

Every file is opened read-only. Nothing is deleted, moved, renamed, rewritten, or "cleaned up".
There is no cache directory, no lock file, no temp copy, no sidecar metadata. Run it twice and the
directory's hashes, sizes and mtimes are byte-for-byte identical. A dedicated test enforces this.

That makes it safe to run on:

- production boxes and CI runners where you only have read access,
- mounted or read-only volumes,
- repositories mid-rebase, mid-`git stash`, or with uncommitted work,
- anything you would rather not let a tool "tidy up".

## Features

- **65+ languages** detected by extension, well-known filenames (`Dockerfile`, `Makefile`,
  `CMakeLists.txt`, `Rakefile`…) and `#!` shebangs.
- **Real comment counting** — per-language line comments, block comments and multi-line strings
  are tracked across lines, so `#` inside a Python string is not mistaken for a comment.
- **Four numbers that matter**: code, comments, blank and total lines — per file and per language.
- **Language share** by code lines and by bytes, so you can see where the weight really is.
- **Structure**: file counts, binary detection, largest and densest files.
- **`.gitignore` aware** — honours your existing rules (including `!` negation), and can be
  switched off entirely with `--no-gitignore`.
- **Zero runtime dependencies** — Python standard library only.
- **Blazing fast** — single-pass walk with `os.scandir`, no subprocesses, no git calls.
- **Typed** — ships `py.typed`, full annotations, no `# type: ignore` smoke.

## Install

```bash
pip install hmh
```

Requires Python 3.9+.

## Command line

```bash
hmh .                                  # summary table for the current directory
hmh ~/projects/myapp --top 10          # only the 10 biggest languages
hmh . --files 5                        # also list the 5 densest source files
hmh . --format markdown -o REPORT.md   # embeddable table for docs
hmh . --format json | jq '.totals'     # machine-readable
hmh . --format csv > stats.csv         # spreadsheet-ready
hmh --languages                        # every language hmh knows
```

| Option | Meaning |
| --- | --- |
| `--format {table,json,csv,markdown}` | Output format (default `table`) |
| `--top N` | Show only the N largest languages |
| `--sort {code,lines,files,bytes,name}` | Ordering of the language table |
| `--files N` | Also list the N densest source files |
| `--exclude PATTERN` | Extra gitignore-style pattern to skip (repeatable) |
| `--include-hidden` | Also walk dot-directories (`.github`, `.venv`, …) |
| `--no-gitignore` | Ignore `.gitignore` and scan everything |
| `--follow-symlinks` | Traverse symlinks instead of skipping them |
| `--max-file-mb N` | Skip line-counting above this size (default 20) |
| `-o, --out FILE` | Write the report to a file |
| `-q, --quiet` | Print nothing; only the exit code |

Exit codes: `0` success, `2` bad path or unreadable project.

## Python API

```python
import hmh

report = hmh.analyze("~/projects/myapp")

print(report.code_lines)        # 54120
print(len(report.languages))    # 6
print(report.size_human)        # '5.4 MB'

for lang in report.top(5):
    print(f"{lang.name:<15} {lang.code:>7,}  {lang.share_of(report.code_lines):5.1f}%")
```

`Report` is a plain dataclass — inspect it, serialize it, or render it:

```python
report.to_dict()                                  # nested dict, ready for JSON
report.languages_by_code                          # sorted
report.languages_by_bytes
report.densest_files                              # biggest source files by code lines
report.largest_files                              # biggest files by bytes
report.comments_per_code                          # density signal

hmh.format_report(report, "markdown")            # same renderer the CLI uses
```

Analyse several projects at once:

```python
for report in hmh.analyze_many(["./api", "./web", "./infra"]):
    print(report.root, report.code_lines)
```

Need the raw numbers without a walk? `hmh.languages.count_lines(text, "Python")` returns
`(code, comment, blank)` for any string.

## How it detects languages

`hmh` resolves a file's language in this order:

1. **Known filename** — `Dockerfile`, `Makefile`, `CMakeLists.txt`, `Rakefile`, `Gemfile`, `BUILD`.
2. **Extension** — `.py`, `.tsx`, `.rs`, `.go`, `.vue`, `.tf`, `.proto`, `.nix`, …
3. **Shebang** — `#!/usr/bin/env python3` → Python, even without an extension.

Anything else is `unknown`. Files containing a NUL byte in the first 8 KB are treated as binary:
they are counted by size, never parsed.

## How it counts lines

Counting is a small state machine that walks each line character by character, tracking:

- whether we are inside a **block comment** (`/* … */`, `<!-- … -->`, `{- … -}`),
- whether we are inside a **multi-line string** (`""" … """` in Python),
- whether a **line comment** (`#`, `//`, `--`, `%`, `;`) starts after real code.

That last point is why `int x; // trailing` counts as **code**, not as a comment — and why a
docstring counts as code, not as documentation. Languages with no comment syntax (JSON, CSV,
Markdown) count every non-blank line as code, matching how `cloc` and `tokei` behave.

## What is skipped

By default `hmh` never walks into dependency and build directories, because they are reproducible
noise rather than your project:

```text
.git  .hg  .svn  node_modules  __pycache__  .venv  venv  .tox  .nox
.mypy_cache  .pytest_cache  .ruff_cache  .next  .nuxt  target  build
dist  vendor  coverage  .gradle  .idea  .vscode  …
```

Add `--include-hidden` to walk dot-directories, or `--no-gitignore` to scan absolutely
everything. Explicit `--exclude` patterns always win.

> `.env*` files are never reported on, so secrets do not end up in a shared report.

## Comparisons

| | `hmh` | `cloc` | `tokei` | `scc` |
| --- | --- | --- | --- | --- |
| Runtime deps | **none** (Python) | Perl binary | Rust binary | Go binary |
| Read-only guarantee | **enforced + tested** | ✅ | ✅ | ✅ |
| `.gitignore` support | built-in | ❌ | partial | partial |
| JSON / CSV / Markdown out | **all four** | JSON | JSON | JSON |
| Install | `pip install hmh` | package manager | `cargo install` | binary download |

## Development

```bash
git clone https://github.com/mrhamidrezam/hmh
cd hmh
python -m venv .venv && .venv\Scripts\activate      # or: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The test suite is fast and **touches no network**: language detection, the comment state machine,
the `.gitignore` matcher, the analyzer, every formatter, and the CLI end-to-end.

A source-integrity test hashes every file before and after analysis and asserts nothing changed.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Hamidreza Moghaddam Kohi** — Full Stack Developer · AI · Automation
Website: <https://hamidrezamoghaddam.ir/> · Email: <info@hamidrezamoghaddam.ir>
