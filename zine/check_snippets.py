#!/usr/bin/env python3
"""Fail if a code snippet in zine.md has drifted from the file it claims.

The zine's whole credibility rests on "lifted from code that actually runs".
This is the check that keeps that true, and it is only a check — the snippets
stay written out in zine.md so the Markdown still reads on GitHub.

A snippet opts in by naming its source file in the first line, as a comment:

    ```python
    # app/models.py
    ...
    ```

Snippets may be trimmed — the zine often shows only the lines under
discussion — so the rule is subsequence, not equality: every non-blank line of
the snippet must appear in the source file, in order. Omitting lines is fine;
inventing or editing one is not.

Needs no dependencies: run it with plain `python3 zine/check_snippets.py`.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```(\w+)?\n(.*?)^```$", re.M | re.S)
MARKER = re.compile(r"^(?:#|//)\s*(\S+\.(?:py|ts|tsx))\s*$")


def source_for(named: str) -> pathlib.Path:
    """zine.md names files relative to their own app; .py is the backend."""
    app = "backend" if named.endswith(".py") else "frontend"
    return ROOT / "app" / app / named


def drift(snippet: list[str], source: list[str]) -> str | None:
    """Return the first snippet line that isn't found, in order, in source."""
    remaining = iter(source)
    for line in snippet:
        if not any(line == candidate for candidate in remaining):
            return line
    return None


def main() -> int:
    text = (ROOT / "zine" / "zine.md").read_text(encoding="utf-8")
    checked = failures = 0

    for _lang, block in FENCE.findall(text):
        lines = block.splitlines()
        if not lines:
            continue
        named = MARKER.match(lines[0].strip())
        if not named:
            continue

        path = source_for(named.group(1))
        if not path.exists():
            print(f"FAIL {named.group(1)}: no such file ({path})")
            failures += 1
            continue

        checked += 1
        snippet = [ln.rstrip() for ln in lines[1:] if ln.strip()]
        source = [ln.rstrip() for ln in path.read_text(encoding="utf-8").splitlines()]

        if missing := drift(snippet, source):
            print(f"FAIL {named.group(1)}: snippet line not found in source, in order:")
            print(f"       {missing.strip()}")
            failures += 1

    print(f"checked {checked} snippet(s), {failures} drifted")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
