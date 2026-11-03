"""Print GitHub release notes for a version, built from CHANGELOG.md.

    python scripts/release_notes.py 0.1.0

Fails (exit 1) if CHANGELOG.md has no "## [0.1.0]" section, so a release can't go out
without notes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INSTALL = """## Install

```bash
pip install kunji           # Windows, macOS, Linux (Python 3.11+)
```

If `pip` isn't found: `python -m pip install kunji` (Windows) or
`python3 -m pip install kunji` (macOS/Linux). Upgrading? `pip install -U kunji`.

No Python on Windows? Download **kunji-windows-x64.exe** below, rename it to `kunji.exe`
and run it from a terminal. Linux: **kunji-linux-x64**.

Then:

```bash
kunji keys add
kunji
```
"""


def section(changelog: str, version: str) -> str | None:
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", re.S | re.M
    )
    match = pattern.search(changelog)
    return match.group(1).strip() if match else None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: release_notes.py <version>", file=sys.stderr)
        return 2
    version = sys.argv[1].removeprefix("v")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    body = section(changelog, version)
    if not body:
        print(f"CHANGELOG.md has no '## [{version}]' section", file=sys.stderr)
        return 1
    print(f"{body}\n\n{INSTALL}\nFull changelog: "
          f"https://github.com/testwithsuraj/kunji/blob/v{version}/CHANGELOG.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
