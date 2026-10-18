"""Command line interface: ``hami .`` or ``hami --format json .``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from . import __version__
from .analyzer import analyze
from .formatters import FORMATS, format_report
from .languages import known_languages

SORTS = ("code", "lines", "files", "bytes", "name")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hami",
        description="Analyse a project without modifying a single byte:\n"
        "lines of code, languages, sizes and structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  hami .\n"
            "  hami ~/projects/myapp --top 10 --files 5\n"
            "  hami . --format markdown -o REPORT.md\n"
            "  hami . --format json | jq '.totals'\n"
            "  hami --languages\n"
        ),
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="directory (or single file) to analyse (default: current directory)",
    )

    show = parser.add_argument_group("what to show")
    show.add_argument("--format", choices=FORMATS, default="table")
    show.add_argument("--top", type=int, metavar="N", help="only the N biggest languages")
    show.add_argument("--sort", choices=SORTS, default="code")
    show.add_argument("--files", type=int, default=0, metavar="N",
                      help="also list the N largest source files")
    show.add_argument("--languages", action="store_true",
                      help="print every language hami knows and exit")

    walk = parser.add_argument_group("scanning")
    walk.add_argument("--include-hidden", action="store_true",
                      help="also walk dot-directories (.github, .venv, …)")
    walk.add_argument("--no-gitignore", action="store_true",
                      help="ignore the project's .gitignore and scan everything")
    walk.add_argument("--exclude", action="append", default=[], metavar="PATTERN",
                      help="extra gitignore-style pattern to skip (repeatable)")
    walk.add_argument("--follow-symlinks", action="store_true")
    walk.add_argument("--max-file-mb", type=int, default=20, metavar="MB",
                      help="skip line-counting above this size (default: 20)")

    out = parser.add_argument_group("output")
    out.add_argument("-o", "--out", metavar="FILE", help="write the report to a file")
    out.add_argument("-q", "--quiet", action="store_true", help="print nothing, only the exit code")
    parser.add_argument("--version", action="version", version=f"hami {__version__}")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles
    except (AttributeError, OSError):
        pass

    if args.languages:
        print("\n".join(known_languages()))
        return 0

    try:
        report = analyze(
            args.path,
            include_hidden=args.include_hidden,
            exclude=args.exclude,
            respect_gitignore=not args.no_gitignore,
            follow_symlinks=args.follow_symlinks,
            max_file_bytes=args.max_file_mb * 1_000_000,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - defensive
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    rendered = format_report(
        report, args.format, top=args.top, sort=args.sort, show_files=args.files
    )

    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8", newline="\n")
        if not args.quiet:
            print(f"wrote {args.out}", file=sys.stderr)
    elif not args.quiet:
        print(rendered)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
