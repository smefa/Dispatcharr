#!/usr/bin/env python3
"""Refresh the fork's managed README section without replacing upstream text."""

import argparse
from pathlib import Path


START = "<!-- xc-profile-fork:start -->"
END = "<!-- xc-profile-fork:end -->"
DOCUMENTATION = Path(__file__).resolve().parents[1] / "docs" / "xc-output-profiles.md"


def update_readme(readme):
    original = readme.read_text(encoding="utf-8")
    documentation = DOCUMENTATION.read_text(encoding="utf-8").strip()
    if not documentation or START in documentation or END in documentation:
        raise ValueError("Fork documentation must be nonempty and contain no managed markers.")
    section = f"{START}\n{documentation}\n{END}"
    if START not in original and END not in original:
        updated = section + "\n\n" + original
    else:
        if original.count(START) != 1 or original.count(END) != 1:
            raise ValueError("README must contain exactly one pair of fork section markers.")
        start = original.index(START)
        end = original.index(END)
        if end < start:
            raise ValueError("README fork section markers are out of order.")
        updated = original[:start] + section + original[end + len(END):]
    if updated != original:
        readme.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", type=Path)
    args = parser.parse_args()
    update_readme(args.readme)


if __name__ == "__main__":
    main()
