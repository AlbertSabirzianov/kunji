import httpx
from typer.testing import CliRunner

from kunji import __version__, keystore
from kunji.cli import app
from kunji.config import Config
from kunji.engine import fallback_chain, stream_turn
from kunji.providers import BUILTIN, Message

runner = CliRunner()


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0 and __version__ in result.output


def test_welcome_when_nothing_configured():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "kunji keys add" in result.output


def test_providers_list():
    result = runner.invoke(app, ["providers"])
    assert result.exit_code == 0
    for pid in ("openai", "anthropic", "gemini", "ollama"):
        assert pid in result.output


def test_keys_add_from_stdin_without_verify_then_list_and_remove():
    result = runner.invoke(
        app,
        ["keys", "add", "groq", "--key-stdin", "--no-verify", "--model", "llama-x"],
        input="gsk_abcdefghijklmnop\n",
    )
    assert result.exit_code == 0, result.output
    assert keystore.get_key("groq")[0] == "gsk_abcdefghijklmnop"
    cfg = Config.load()
    assert cfg.get("default_model") == "groq:llama-x"

    listed = runner.invoke(app, ["keys", "list"])
    assert "groq" in listed.output and "gsk_abcdefghijklmnop" not in listed.output

    removed = runner.invoke(app, ["keys", "remove", "groq", "--yes"])
    assert removed.exit_code == 0
    assert keystore.get_key("groq")[0] is None
    assert Config.load().get("default_model") == ""


def test_config_set_and_get():
    assert runner.invoke(app, ["config", "set", "display.currency", "INR"]).exit_code == 0
    assert "INR" in runner.invoke(app, ["config", "get", "display.currency"]).output
    assert runner.invoke(app, ["config", "set", "nope.x", "1"]).exit_code == 2


def test_budget_commands():
    assert runner.invoke(app, ["budget", "set", "openai", "2"]).exit_code == 0
    shown = runner.invoke(app, ["budget", "show"])
    assert "openai" in shown.output
    assert runner.invoke(app, ["budget", "clear", "openai"]).exit_code == 0


def test_custom_provider_validation():
    ok = runner.invoke(
        app, ["providers", "add", "lmstudio", "--base-url", "http://localhost:1234/v1", "--no-key"]
    )
    assert ok.exit_code == 0
    assert "lmstudio" in runner.invoke(app, ["providers"]).output
    bad = runner.invoke(app, ["providers", "add", "openai", "--base-url", "https://x"])
    assert bad.exit_code == 2


def test_stream_turn_records_usage_and_estimates():
    def handler(request):
        return httpx.Response(
            200, content=b'data: {"choices":[{"delta":{"content":"hey"}}]}\n\ndata: [DONE]\n\n'
        )

    cfg = Config.load()
    result = stream_turn(
        cfg,
        BUILTIN["ollama"],
        "llama",
        [Message("user", "hi")],
        transport=httpx.MockTransport(handler),
    )
    assert result.text == "hey" and result.usage.estimated
    from kunji import usage

    assert usage.summary(1)[0].requests == 1


def test_fallback_chain_skips_missing_keys():
    cfg = Config.load()
    cfg.set("fallback", ["groq:llama", "ollama:qwen"])
    chain = fallback_chain(cfg, BUILTIN["openai"], "gpt")
    assert [f"{s.id}:{m}" for s, m in chain] == ["openai:gpt", "ollama:qwen"]


def test_models_rejects_non_positive_limit():
    for limit in ("0", "-1"):
        result = runner.invoke(
            app,
            ["models", "openai", "--limit", limit],
        )

        assert result.exit_code == 2
        assert "greater than 0" in result.output
