"""Keep kunji's all-time PyPI download count and write the README badge.

Run once a day by .github/workflows/downloads.yml. pypistats.org only keeps the last 180 days,
so every run merges the days it returns into a history file that is kept forever, on the
`stats` branch. The total is the sum of that history (downloads from PyPI mirrors excluded).

    python scripts/download_stats.py <history.json> <badge.json>

The badge file is a shields.io "endpoint" badge:
    https://img.shields.io/endpoint?url=<raw URL of badge.json>
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path

PACKAGE = "kunji"
LABEL = "downloads"
COLOR = "2563eb"  # README badge blue
LABEL_COLOR = "1f2328"


def fetch_daily(package: str = PACKAGE) -> dict[str, int]:
    """Daily downloads for the last 180 days from pypistats.org, without mirrors."""
    import pypistats

    raw = pypistats.overall(package, mirrors=False, total="daily", format="json")
    try:
        data = json.loads(raw)["data"]
    except (ValueError, KeyError, TypeError) as exc:  # "No data found ..." or a changed API
        raise RuntimeError(f"Unexpected answer from pypistats.org: {str(raw)[:200]}") from exc
    return {
        row["date"]: int(row["downloads"])
        for row in data
        if row.get("category") == "without_mirrors"
    }


def merge(history: dict[str, int], latest: dict[str, int]) -> dict[str, int]:
    """Add the latest days. Days pypistats returns again replace the stored ones, because
    the newest day can still grow; days it no longer returns (older than 180) are kept."""
    merged = dict(history)
    merged.update(latest)
    return dict(sorted(merged.items()))


def short(n: int) -> str:
    """1234 -> '1.2k', 1_234_567 -> '1.2M' (like the other badges)."""
    for size, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if n >= size:
            value = f"{n / size:.1f}".removesuffix(".0")
            return f"{value}{suffix}"
    return str(n)


def badge(total: int) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "label": LABEL,
        "message": short(total),
        "color": COLOR,
        "labelColor": LABEL_COLOR,
    }


def run(history_path: Path, badge_path: Path, fetch: Callable[[], dict[str, int]]) -> int:
    history: dict[str, int] = {}
    if history_path.exists():
        history = {k: int(v) for k, v in json.loads(history_path.read_text())["daily"].items()}
    daily = merge(history, fetch())
    total = sum(daily.values())
    history_path.write_text(
        json.dumps({"package": PACKAGE, "total": total, "daily": daily}, indent=1) + "\n"
    )
    badge_path.write_text(json.dumps(badge(total)) + "\n")
    return total


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    total = run(Path(sys.argv[1]), Path(sys.argv[2]), fetch_daily)
    print(f"{PACKAGE}: {total} downloads ({short(total)})")


if __name__ == "__main__":
    main()
