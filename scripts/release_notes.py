"""Print GitHub release notes for a version, built from CHANGELOG.md and docs/COMMANDS.md.

    python scripts/release_notes.py 0.1.1

Fails (exit 1) if CHANGELOG.md has no "## [0.1.1]" section, so a release can't go out
without notes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/testwithsuraj/kunji"

INTRO = """**Your keys. Every AI model. One terminal.**

kunji is a free, open-source chat app for your terminal. Bring your own API key from any
provider, switch models mid-conversation, and see what every reply costs."""

INSTALL = """## Install or upgrade

| | Command |
| --- | --- |
| New install | `pip install kunji` |
| Already installed (0.1.1 or newer) | `kunji upgrade` |
| Upgrading from 0.1.0 | `pip install --upgrade kunji` |

If `pip` isn't found, use `python -m pip install --upgrade kunji` on Windows or
`python3 -m pip install --upgrade kunji` on macOS and Linux.
No Python on Windows? Download **kunji-windows-x64.exe** below and run it from a terminal.
Linux: **kunji-linux-x64**.

Then just run `kunji`: the menu walks you through adding a key and starting a chat."""

FOOTER = f"""## Feedback

⭐ [Star kunji]({REPO}) if it's useful · 🐛 [Report a problem]({REPO}/issues/new/choose) ·
🌐 [Website](https://testwithsuraj.github.io/kunji/)

Check downloads against `SHA256SUMS.txt`."""


def section(changelog: str, version: str) -> str | None:
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", re.S | re.M
    )
    match = pattern.search(changelog)
    return match.group(1).strip() if match else None


def command_guide() -> str:
    path = ROOT / "docs" / "COMMANDS.md"
    if not path.exists():
        return ""
    body = path.read_text(encoding="utf-8")
    body = re.sub(r"^# .*\n", "", body, count=1).strip()
    body = body.replace("](CONFIG.md)", f"]({REPO}/blob/main/docs/CONFIG.md)")
    return (
        "<details>\n<summary><b>How to use every command</b> (click to open)</summary>\n\n"
        f"{body}\n\n</details>"
    )


def build(version: str) -> str | None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    body = section(changelog, version)
    if not body:
        return None
    parts = [INTRO, "## What's new", body.replace("### ", "#### "), INSTALL]
    guide = command_guide()
    if guide:
        parts.append(guide)
    parts += [FOOTER, f"Full changelog: {REPO}/blob/v{version}/CHANGELOG.md"]
    return "\n\n".join(parts)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: release_notes.py <version>", file=sys.stderr)
        return 2
    version = sys.argv[1].removeprefix("v")
    notes = build(version)
    if notes is None:
        print(f"CHANGELOG.md has no '## [{version}]' section", file=sys.stderr)
        return 1
    print(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
