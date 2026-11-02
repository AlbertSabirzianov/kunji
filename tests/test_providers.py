import json

import httpx
import pytest

from kunji.config import Config
from kunji.providers import BUILTIN, Message, ProviderError, make_provider, parse_ref, resolve_ref


def sse(*events: dict | str) -> bytes:
    lines = []
    for e in events:
        lines.append("data: " + (e if isinstance(e, str) else json.dumps(e)))
        lines.append("")
    return ("\n".join(lines) + "\n").encode()


def test_parse_ref_keeps_colons_in_model():
    assert parse_ref("ollama:qwen2.5:7b") == ("ollama", "qwen2.5:7b")
    assert parse_ref("openai") == ("openai", "")


def test_openai_stream_text_and_usage():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        body = sse(
            {"choices": [{"delta": {"content": "Hel"}}]},
            {"choices": [{"delta": {"content": "lo"}}]},
            {"choices": [], "usage": {"prompt_tokens": 7, "completion_tokens": 2}},
            "[DONE]",
        )
        return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

    p = make_provider(BUILTIN["openai"], api_key="sk-test-123456789",
                      transport=httpx.MockTransport(handler))
    events = list(p.stream("gpt-x", [Message("user", "hi")], system="be brief"))
    assert "".join(e.text for e in events if e.text) == "Hello"
    usage = [e.usage for e in events if e.usage][-1]
    assert (usage.input_tokens, usage.output_tokens) == (7, 2)
    assert seen["body"]["messages"][0] == {"role": "system", "content": "be brief"}
    assert seen["body"]["max_completion_tokens"] == 4096
    assert seen["auth"] == "Bearer sk-test-123456789"


def test_retries_without_stream_options_when_unsupported():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if "stream_options" in body:
            return httpx.Response(400, json={"error": {"message": "Unknown field stream_options"}})
        return httpx.Response(200, content=sse({"choices": [{"delta": {"content": "ok"}}]},
                                                "[DONE]"))

    p = make_provider(BUILTIN["groq"], api_key="gsk_abcdefghijkl",
                      transport=httpx.MockTransport(handler))
    text = "".join(e.text for e in p.stream("m", [Message("user", "x")]) if e.text)
    assert text == "ok"
    assert len(calls) == 2 and "stream_options" not in calls[1]
    assert calls[1]["max_tokens"] == 4096


def test_anthropic_stream():
    events_body = "\n".join([
        "event: message_start",
        'data: {"type":"message_start","message":{"usage":{"input_tokens":11}}}',
        "",
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}',
        "",
        'data: {"type":"message_delta","usage":{"output_tokens":3}}',
        "",
        'data: {"type":"message_stop"}',
        "",
    ]).encode()

    def handler(request):
        assert request.headers["x-api-key"] == "sk-ant-abcdefghijkl"
        assert request.headers["anthropic-version"]
        body = json.loads(request.content)
        assert body["system"] == "sys"
        return httpx.Response(200, content=events_body)

    p = make_provider(BUILTIN["anthropic"], api_key="sk-ant-abcdefghijkl",
                      transport=httpx.MockTransport(handler))
    events = list(p.stream("claude-x", [Message("user", "hey")], system="sys"))
    assert "".join(e.text for e in events if e.text) == "Hi"
    usage = [e.usage for e in events if e.usage][-1]
    assert (usage.input_tokens, usage.output_tokens) == (11, 3)


def test_auth_error_is_redacted_and_has_hint():
    key = "sk-secret-abcdef1234567890"

    def handler(request):
        return httpx.Response(401, json={"error": {"message": f"Incorrect API key: {key}"}})

    p = make_provider(BUILTIN["openai"], api_key=key, transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError) as info:
        list(p.stream("m", [Message("user", "x")]))
    assert key not in info.value.message
    assert info.value.status == 401
    assert "kunji keys add openai" in info.value.hint


def test_rate_limit_is_retryable():
    p = make_provider(BUILTIN["openai"], api_key="sk-abcdefghijkl",
                      transport=httpx.MockTransport(lambda r: httpx.Response(429, json={})))
    with pytest.raises(ProviderError) as info:
        list(p.stream("m", [Message("user", "x")]))
    assert info.value.retryable


def test_gemini_models_strip_prefix():
    def handler(request):
        return httpx.Response(200, json={"data": [{"id": "models/gemini-flash"}, {"id": "b"}]})

    p = make_provider(BUILTIN["gemini"], api_key="AIza-abcdefghijkl",
                      transport=httpx.MockTransport(handler))
    assert p.list_models() == ["b", "gemini-flash"]


def test_missing_key_gives_hint():
    with pytest.raises(ProviderError) as info:
        make_provider(BUILTIN["openai"])
    assert "kunji keys add openai" in info.value.hint


def test_ollama_needs_no_key():
    p = make_provider(BUILTIN["ollama"])
    assert p.api_key is None


def test_resolve_ref_uses_provider_default(tmp_path):
    cfg = Config.load(tmp_path / "c.toml")
    cfg.set("providers.groq", {"default_model": "llama"})
    spec, model = resolve_ref(cfg, "groq")
    assert (spec.id, model) == ("groq", "llama")
    with pytest.raises(ProviderError):
        resolve_ref(cfg, "nope:x")
