"""Built-in providers plus user-defined OpenAI-compatible servers."""

from __future__ import annotations

import re

import httpx

from kunji.config import Config
from kunji.keystore import get_key
from kunji.providers.anthropic import AnthropicProvider
from kunji.providers.base import Provider, ProviderError, ProviderSpec
from kunji.providers.openai_compat import OpenAICompatProvider

BUILTIN: dict[str, ProviderSpec] = {
    spec.id: spec
    for spec in (
        ProviderSpec(
            "openai", "OpenAI", "openai", "https://api.openai.com/v1",
            env_vars=("OPENAI_API_KEY",), key_url="https://platform.openai.com/api-keys",
            openrouter_prefix="openai",
        ),
        ProviderSpec(
            "anthropic", "Anthropic", "anthropic", "https://api.anthropic.com",
            env_vars=("ANTHROPIC_API_KEY",), key_url="https://console.anthropic.com/settings/keys",
            openrouter_prefix="anthropic",
        ),
        ProviderSpec(
            "gemini", "Google Gemini", "openai",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            env_vars=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            key_url="https://aistudio.google.com/apikey", openrouter_prefix="google",
        ),
        ProviderSpec(
            "groq", "Groq", "openai", "https://api.groq.com/openai/v1",
            env_vars=("GROQ_API_KEY",), key_url="https://console.groq.com/keys",
        ),
        ProviderSpec(
            "openrouter", "OpenRouter", "openai", "https://openrouter.ai/api/v1",
            env_vars=("OPENROUTER_API_KEY",), key_url="https://openrouter.ai/keys",
            openrouter_prefix="",
        ),
        ProviderSpec(
            "deepseek", "DeepSeek", "openai", "https://api.deepseek.com/v1",
            env_vars=("DEEPSEEK_API_KEY",), key_url="https://platform.deepseek.com/api_keys",
            openrouter_prefix="deepseek",
        ),
        ProviderSpec(
            "mistral", "Mistral", "openai", "https://api.mistral.ai/v1",
            env_vars=("MISTRAL_API_KEY",), key_url="https://console.mistral.ai/api-keys",
            openrouter_prefix="mistralai",
        ),
        ProviderSpec(
            "xai", "xAI", "openai", "https://api.x.ai/v1",
            env_vars=("XAI_API_KEY",), key_url="https://console.x.ai",
            openrouter_prefix="x-ai",
        ),
        ProviderSpec(
            "together", "Together AI", "openai", "https://api.together.xyz/v1",
            env_vars=("TOGETHER_API_KEY",), key_url="https://api.together.ai/settings/api-keys",
        ),
        ProviderSpec(
            "ollama", "Ollama (local)", "openai", "http://localhost:11434/v1",
            needs_key=False, key_url="https://ollama.com/download",
        ),
    )
}

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")


def valid_provider_id(value: str) -> bool:
    return bool(_ID_RE.match(value))


def all_specs(cfg: Config) -> dict[str, ProviderSpec]:
    specs = dict(BUILTIN)
    for pid, entry in (cfg.get("custom_providers") or {}).items():
        if not isinstance(entry, dict) or not entry.get("base_url") or not valid_provider_id(pid):
            continue
        specs[pid] = ProviderSpec(
            pid,
            str(entry.get("name") or pid),
            "openai",
            str(entry["base_url"]),
            needs_key=bool(entry.get("needs_key", True)),
            custom=True,
        )
    # Allow overriding the base URL of built-ins (e.g. remote Ollama, proxies).
    for pid, entry in (cfg.get("providers") or {}).items():
        if pid in specs and isinstance(entry, dict) and entry.get("base_url"):
            s = specs[pid]
            specs[pid] = ProviderSpec(
                s.id, s.name, s.kind, str(entry["base_url"]), s.env_vars, s.needs_key,
                s.key_url, s.openrouter_prefix, s.custom,
            )
    return specs


def get_spec(cfg: Config, provider_id: str) -> ProviderSpec:
    specs = all_specs(cfg)
    if provider_id not in specs:
        known = ", ".join(sorted(specs))
        raise ProviderError(f"Unknown provider '{provider_id}'.", hint=f"Known providers: {known}")
    return specs[provider_id]


def parse_ref(ref: str) -> tuple[str, str]:
    """'anthropic:claude-x' -> ('anthropic', 'claude-x'). Model ids may contain ':'."""
    if ":" not in ref:
        return ref.strip(), ""
    provider, model = ref.split(":", 1)
    return provider.strip(), model.strip()


def resolve_ref(cfg: Config, ref: str | None) -> tuple[ProviderSpec, str]:
    ref = (ref or cfg.get("default_model") or "").strip()
    if not ref:
        raise ProviderError(
            "No model selected yet.",
            hint="Add a provider first: kunji keys add",
        )
    provider_id, model = parse_ref(ref)
    spec = get_spec(cfg, provider_id)
    if not model:
        model = cfg.provider_entry(provider_id).get("default_model", "")
    if not model:
        raise ProviderError(
            f"No model chosen for {spec.name}.",
            hint=f"Pick one: kunji use {provider_id}:<model>   (list: kunji models {provider_id})",
        )
    return spec, model


def key_for(spec: ProviderSpec) -> tuple[str | None, str]:
    if not spec.needs_key:
        return None, "not needed"
    return get_key(spec.id, spec.env_vars)


def make_provider(
    spec: ProviderSpec,
    api_key: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> Provider:
    if api_key is None and spec.needs_key:
        api_key, _ = key_for(spec)
        if not api_key:
            raise ProviderError(
                f"No API key found for {spec.name}.",
                hint=f"Add one with: kunji keys add {spec.id}",
            )
    cls = AnthropicProvider if spec.kind == "anthropic" else OpenAICompatProvider
    return cls(spec, api_key, transport=transport)
