"""One request/answer turn: stream, measure, price and record usage."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from kunji import usage as ledger
from kunji.catalog import Catalog
from kunji.config import Config
from kunji.providers import Message, ProviderError, ProviderSpec, Usage, make_provider
from kunji.providers.base import estimate_tokens
from kunji.providers.registry import get_spec, key_for, parse_ref


@dataclass
class TurnResult:
    spec: ProviderSpec
    model: str
    text: str
    usage: Usage
    cost_usd: float | None
    elapsed: float
    interrupted: bool = False

    @property
    def ref(self) -> str:
        return f"{self.spec.id}:{self.model}"


def stream_turn(
    cfg: Config,
    spec: ProviderSpec,
    model: str,
    messages: list[Message],
    system: str = "",
    on_text: Callable[[str], None] | None = None,
    catalog: Catalog | None = None,
    transport: httpx.BaseTransport | None = None,
    record: bool = True,
) -> TurnResult:
    catalog = catalog or Catalog(cfg)
    max_tokens = int(cfg.get("chat.max_tokens", 4096) or 4096)
    started = time.monotonic()
    parts: list[str] = []
    usage: Usage | None = None
    interrupted = False
    with make_provider(spec, transport=transport) as provider:
        try:
            for event in provider.stream(model, messages, system=system, max_tokens=max_tokens):
                if event.text:
                    parts.append(event.text)
                    if on_text:
                        on_text(event.text)
                if event.usage:
                    usage = event.usage
        except KeyboardInterrupt:
            interrupted = True
    text = "".join(parts)
    if usage is None or usage.total == 0:
        prompt_chars = system + "".join(m.content for m in messages)
        usage = Usage(estimate_tokens(prompt_chars), estimate_tokens(text), estimated=True)
    cost = catalog.cost(spec.id, model, spec.openrouter_prefix, usage.input_tokens,
                        usage.output_tokens)
    if record and (text or usage.input_tokens):
        ledger.record(spec.id, model, usage.input_tokens, usage.output_tokens, cost,
                      usage.estimated)
    return TurnResult(spec, model, text, usage, cost, time.monotonic() - started, interrupted)


def fallback_chain(cfg: Config, spec: ProviderSpec, model: str) -> list[tuple[ProviderSpec, str]]:
    chain = [(spec, model)]
    seen = {f"{spec.id}:{model}"}
    for ref in cfg.get("fallback") or []:
        pid, m = parse_ref(str(ref))
        try:
            fspec = get_spec(cfg, pid)
        except ProviderError:
            continue
        m = m or cfg.provider_entry(pid).get("default_model", "")
        if not m or f"{pid}:{m}" in seen:
            continue
        if fspec.needs_key and not key_for(fspec)[0]:
            continue
        seen.add(f"{pid}:{m}")
        chain.append((fspec, m))
    return chain
