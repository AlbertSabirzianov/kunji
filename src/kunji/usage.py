"""Local usage ledger and daily budgets. Stays on this machine only."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from kunji.catalog import to_display
from kunji.config import Config, data_dir, ensure_dir

WARN_AT = 0.8


def ledger_path() -> Path:
    return data_dir() / "usage.jsonl"


def record(provider: str, model: str, input_tokens: int, output_tokens: int,
           cost_usd: float | None, estimated: bool = False) -> None:
    entry = {
        "ts": time.time(),
        "provider": provider,
        "model": model,
        "in": int(input_tokens),
        "out": int(output_tokens),
        "cost": None if cost_usd is None else round(cost_usd, 8),
        "est": bool(estimated),
    }
    path = ledger_path()
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def entries(since: float = 0.0) -> list[dict]:
    path = ledger_path()
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if float(item.get("ts", 0)) >= since:
                out.append(item)
    return out


def start_of_day(day: date | None = None) -> float:
    day = day or date.today()
    return datetime(day.year, day.month, day.day).timestamp()


def spent_today_usd(provider: str | None = None) -> float:
    total = 0.0
    for item in entries(start_of_day()):
        if provider and item.get("provider") != provider:
            continue
        total += float(item.get("cost") or 0.0)
    return total


@dataclass
class Row:
    provider: str
    model: str
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    unknown_cost: int = 0


def summary(days: int = 7) -> list[Row]:
    since = start_of_day(date.today() - timedelta(days=max(days, 1) - 1))
    rows: dict[tuple[str, str], Row] = defaultdict(lambda: Row("", ""))
    for item in entries(since):
        key = (item.get("provider", "?"), item.get("model", "?"))
        row = rows[key]
        row.provider, row.model = key
        row.requests += 1
        row.input_tokens += int(item.get("in") or 0)
        row.output_tokens += int(item.get("out") or 0)
        if item.get("cost") is None:
            row.unknown_cost += 1
        else:
            row.cost_usd += float(item["cost"])
    return sorted(rows.values(), key=lambda r: (-r.cost_usd, r.provider, r.model))


@dataclass
class BudgetStatus:
    state: str  # "ok" | "warn" | "block" | "none"
    scope: str = ""
    spent: float = 0.0  # display currency
    limit: float = 0.0  # display currency


def check_budget(cfg: Config, provider: str) -> BudgetStatus:
    """Budgets are set in the display currency, e.g. 200 with currency INR."""
    limits = cfg.get("budget.daily") or {}
    worst = BudgetStatus("none")
    order = {"none": 0, "ok": 1, "warn": 2, "block": 3}
    for scope in (provider, "all"):
        if scope not in limits:
            continue
        try:
            limit = float(limits[scope])
        except (TypeError, ValueError):
            continue
        if limit <= 0:
            continue
        spent = to_display(cfg, spent_today_usd(None if scope == "all" else provider))
        state = "block" if spent >= limit else "warn" if spent >= limit * WARN_AT else "ok"
        status = BudgetStatus(state, scope, spent, limit)
        if order[state] > order[worst.state]:
            worst = status
    return worst
