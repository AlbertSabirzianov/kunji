"""Anthropic Messages API (native format)."""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from kunji.providers.base import (
    Message,
    Provider,
    ProviderError,
    StreamEvent,
    Usage,
    iter_sse_data,
)

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(Provider):
    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key or "",
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def list_models(self) -> list[str]:
        try:
            response = self.client.get(
                self._url("/v1/models"), params={"limit": 1000}, headers=self._headers()
            )
        except httpx.HTTPError as exc:
            raise self._network_error(exc) from exc
        if response.status_code != 200:
            raise self._error_from_response(response)
        return sorted({item["id"] for item in response.json().get("data", []) if "id" in item})

    def stream(
        self,
        model: str,
        messages: list[Message],
        system: str = "",
        max_tokens: int = 4096,
    ) -> Iterator[StreamEvent]:
        body: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        if system:
            body["system"] = system
        try:
            with self.client.stream(
                "POST", self._url("/v1/messages"), json=body, headers=self._headers()
            ) as response:
                if response.status_code != 200:
                    raise self._error_from_response(response)
                yield from self._parse(response)
        except httpx.HTTPError as exc:
            raise self._network_error(exc) from exc

    def _parse(self, response: httpx.Response) -> Iterator[StreamEvent]:
        input_tokens = 0
        for data in iter_sse_data(response):
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            kind = obj.get("type")
            if kind == "message_start":
                usage = (obj.get("message") or {}).get("usage") or {}
                input_tokens = int(usage.get("input_tokens") or 0)
            elif kind == "content_block_delta":
                delta = obj.get("delta") or {}
                if delta.get("type") == "text_delta" and delta.get("text"):
                    yield StreamEvent(text=delta["text"])
            elif kind == "message_delta":
                usage = obj.get("usage") or {}
                yield StreamEvent(
                    usage=Usage(
                        input_tokens=int(usage.get("input_tokens") or input_tokens),
                        output_tokens=int(usage.get("output_tokens") or 0),
                    )
                )
            elif kind == "error":
                err = obj.get("error") or {}
                retryable = err.get("type") in {"overloaded_error", "rate_limit_error"}
                raise ProviderError(
                    f"{self.spec.name}: {err.get('message', 'stream error')}", retryable=retryable
                )
            elif kind == "message_stop":
                break
