"""Minimal hami examples.

Run after ``pip install hami``::

    python examples/quickstart.py .
"""

from __future__ import annotations

import sys

import hami


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    report = hami.analyze(target)

    print(f"Project      {report.root}")
    print(f"Files        {report.total_files:,} "
          f"({report.source_files:,} source · {report.binary_files:,} binary)")
    print(f"Size         {report.size_human}")
    print(f"Code lines   {report.code_lines:,}")
    print(f"Comments     {report.comment_lines:,} "
          f"({report.comments_per_code} per code line)")
    print(f"Languages    {len(report.languages)}")
    print()

    print(f"{'LANGUAGE':<24}{'FILES':>8}{'CODE':>12}{'SHARE':>9}")
    print("-" * 53)
    for stats in report.top(10):
        print(
            f"{stats.name:<24}{stats.files:>8,}{stats.code:>12,}"
            f"{stats.share_of(report.code_lines):>8.1f}%"
        )

    biggest = report.densest_files[:3]
    if biggest:
        print()
        print("Densest files")
        for item in biggest:
            print(f"  {item.code:>7,} code  {item.path}")


if __name__ == "__main__":
    main()
