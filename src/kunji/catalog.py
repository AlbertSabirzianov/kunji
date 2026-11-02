"""Model prices for the live cost meter.

Price lookup order (first match wins):
  1. Your own overrides in config:  [pricing."provider:model"] input = 0.15, output = 0.6
  2. Kunji's curated catalog (catalog/pricing.json in the repo, fetched + cached 24h)
  3. OpenRouter's public model list (fetched + cached 24h)

All prices are USD per 1 million tokens. Fetching sends no user data.
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from kunji import __version__
from kunji.config import Config, atomic_write, cache_dir
from kunji.constants import CACHE_TTL_SECONDS, CATALOG_URL, OPENROUTER_MODELS_URL


@dataclass(frozen=True)
class Price:
    input: float  # USD per 1M input tokens
    output: float  # USD per 1M output tokens
    source: str

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.input + output_tokens * self.output) / 1_000_000


_DATE_SUFFIX = re.compile(r"(-\d{8}|-\d{4}-\d{2}-\d{2}|-latest|-preview)$")


def normalize(model_id: str) -> str:
    value = model_id.lower().strip()
    value = re.sub(r"[._:\s]+", "-", value)
    prev = None
    while prev != value:
        prev = value
        value = _DATE_SUFFIX.sub("", value)
    return value


def _cache_file(name: str) -> Path:
    return cache_dir() / name


def _read_cache(name: str) -> dict[str, Any] | None:
    path = _cache_file(name)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _fresh(blob: dict[str, Any] | None) -> bool:
    return bool(blob) and time.time() - float(blob.get("fetched_at", 0)) < CACHE_TTL_SECONDS


def _fetch_json(url: str, timeout: float = 6.0) -> Any:
    with httpx.Client(timeout=timeout, headers={"user-agent": f"kunji/{__version__}"}) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _parse_openrouter(data: Any) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for item in (data or {}).get("data", []):
        try:
            pricing = item.get("pricing") or {}
            prompt = float(pricing.get("prompt", 0)) * 1_000_000
            completion = float(pricing.get("completion", 0)) * 1_000_000
        except (TypeError, ValueError):
            continue
        if prompt < 0 or completion < 0:
            continue
        out[str(item.get("id"))] = [round(prompt, 6), round(completion, 6)]
    return out


def refresh(cfg: Config, force: bool = False) -> None:
    """Refresh cached catalogs. Never raises — prices are a nice-to-have."""
    if not cfg.get("network.catalog", True):
        return
    for name, url, parser in (
        ("openrouter_prices.json", OPENROUTER_MODELS_URL, _parse_openrouter),
        ("kunji_prices.json", CATALOG_URL, lambda d: (d or {}).get("models", {})),
    ):
        if not force and _fresh(_read_cache(name)):
            continue
        try:
            prices = parser(_fetch_json(url))
        except Exception:  # noqa: BLE001, S112 - offline or blocked is fine
            continue
        blob = {"fetched_at": time.time(), "prices": prices}
        try:
            atomic_write(_cache_file(name), json.dumps(blob).encode("utf-8"))
        except OSError:
            pass


def refresh_in_background(cfg: Config) -> threading.Thread:
    thread = threading.Thread(target=refresh, args=(cfg,), daemon=True)
    thread.start()
    return thread


class Catalog:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._kunji = (_read_cache("kunji_prices.json") or {}).get("prices", {})
        self._openrouter = (_read_cache("openrouter_prices.json") or {}).get("prices", {})
        self._or_norm: dict[str, list[float]] = {}
        for key, value in self._openrouter.items():
            self._or_norm.setdefault(normalize(key), value)

    def price_for(self, provider_id: str, model: str, prefix: str | None = None) -> Price | None:
        ref = f"{provider_id}:{model}"
        user = (self.cfg.get("pricing") or {}).get(ref)
        if isinstance(user, dict):
            try:
                return Price(float(user["input"]), float(user["output"]), "your config")
            except (KeyError, TypeError, ValueError):
                pass
        curated = self._kunji.get(ref)
        if isinstance(curated, list | tuple) and len(curated) == 2:
            return Price(float(curated[0]), float(curated[1]), "kunji catalog")

        if prefix is None:
            return None
        or_id = model if prefix == "" else f"{prefix}/{model}"
        hit = self._openrouter.get(or_id) or self._or_norm.get(normalize(or_id))
        if hit:
            return Price(float(hit[0]), float(hit[1]), "openrouter")
        return None

    def cost(self, provider_id, model, prefix, input_tokens, output_tokens) -> float | None:
        price = self.price_for(provider_id, model, prefix)
        return None if price is None else price.cost(input_tokens, output_tokens)


# Money formatting ---------------------------------------------------------------
_SYMBOLS = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}


def to_display(cfg: Config, usd: float) -> float:
    try:
        rate = float(cfg.get("display.usd_rate", 1.0))
    except (TypeError, ValueError):
        rate = 1.0
    return usd * (rate if rate > 0 else 1.0)


def fmt_money(cfg: Config, usd: float | None, *, display_amount: float | None = None) -> str:
    if usd is None and display_amount is None:
        return "—"
    currency = str(cfg.get("display.currency", "USD")).upper()
    symbol = _SYMBOLS.get(currency, currency + " ")
    amount = display_amount if display_amount is not None else to_display(cfg, usd or 0.0)
    if amount == 0:
        return f"{symbol}0"
    if amount < 0.0001:
        return f"<{symbol}0.0001"
    if amount < 0.01:
        return f"{symbol}{amount:.4f}"
    return f"{symbol}{amount:,.2f}"
