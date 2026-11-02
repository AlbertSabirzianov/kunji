import json
import time

from kunji import keystore, usage
from kunji.catalog import Catalog, fmt_money, normalize
from kunji.config import Config, cache_dir, coerce, config_path


def test_config_roundtrip_and_defaults():
    cfg = Config.load()
    assert cfg.get("display.currency") == "USD"
    cfg.set("display.currency", "INR")
    cfg.set("budget.daily.openai", 200)
    cfg.save()
    again = Config.load()
    assert again.get("display.currency") == "INR"
    assert again.get("budget.daily.openai") == 200
    assert again.get("updates.check") is True  # default still merged in
    assert "sk-" not in config_path().read_text()


def test_coerce():
    assert coerce("true") is True and coerce("off") is False
    assert coerce("3") == 3 and coerce("2.5") == 2.5
    assert coerce('["a:b"]') == ["a:b"]
    assert coerce("hello") == "hello"


def test_keys_env_wins_over_keychain(monkeypatch):
    keystore.set_key("openai", "sk-from-keychain-1234")
    assert keystore.get_key("openai", ("OPENAI_API_KEY",)) == ("sk-from-keychain-1234", "keychain")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-12345678")
    assert keystore.get_key("openai", ("OPENAI_API_KEY",))[1] == "env:OPENAI_API_KEY"
    assert keystore.delete_key("openai")
    assert not keystore.delete_key("openai")


def test_mask_and_redact():
    assert keystore.mask("sk-1234567890abcd") == "sk-123••••••••abcd"
    assert keystore.mask("short") == "••••••••"
    secret = "sk-1234567890abcd"
    assert secret not in keystore.redact(f"bad key {secret}", secret)


def test_normalize():
    assert normalize("claude-sonnet-4.5-20250929") == normalize("claude-sonnet-4-5")
    assert normalize("gpt-4o-2024-08-06") == "gpt-4o"


def _write_cache(name, prices):
    path = cache_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched_at": time.time(), "prices": prices}))


def test_price_lookup_order():
    _write_cache("openrouter_prices.json", {"openai/gpt-x": [1.0, 2.0],
                                            "anthropic/claude-z-4.5": [3.0, 15.0]})
    _write_cache("kunji_prices.json", {"groq:llama": [0.5, 0.5]})
    cfg = Config.load()
    cat = Catalog(cfg)
    assert cat.price_for("openai", "gpt-x", "openai").source == "openrouter"
    assert cat.price_for("anthropic", "claude-z-4-5-20250101", "anthropic").input == 3.0
    assert cat.price_for("groq", "llama", None).source == "kunji catalog"
    assert cat.cost("openai", "gpt-x", "openai", 1_000_000, 500_000) == 2.0
    cfg.set("pricing", {"openai:gpt-x": {"input": 9, "output": 9}})
    assert Catalog(cfg).price_for("openai", "gpt-x", "openai").source == "your config"


def test_money_format():
    cfg = Config.load()
    assert fmt_money(cfg, 1.5) == "$1.50"
    assert fmt_money(cfg, 0.0012) == "$0.0012"
    assert fmt_money(cfg, None) == "—"
    cfg.set("display.currency", "INR")
    cfg.set("display.usd_rate", 84)
    assert fmt_money(cfg, 1) == "₹84.00"


def test_budget_states():
    cfg = Config.load()
    cfg.set("budget.daily", {"openai": 1.0})
    assert usage.check_budget(cfg, "openai").state == "ok"
    usage.record("openai", "gpt-x", 10, 10, 0.85)
    assert usage.check_budget(cfg, "openai").state == "warn"
    usage.record("openai", "gpt-x", 10, 10, 0.20)
    assert usage.check_budget(cfg, "openai").state == "block"
    assert usage.check_budget(cfg, "groq").state == "none"
    rows = usage.summary(1)
    assert rows[0].requests == 2 and round(rows[0].cost_usd, 2) == 1.05
