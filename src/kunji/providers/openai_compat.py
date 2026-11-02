"""Any API that speaks the OpenAI chat-completions format.

Covers OpenAI, Gemini (OpenAI-compatible endpoint), Groq, OpenRouter, DeepSeek,
Mistral, xAI, Together, Ollama, LM Studio and custom servers.
"""

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


class OpenAICompatProvider(Provider):
    def _headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"
        if self.spec.id == "openrouter":
            headers["x-title"] = "kunji"
        return headers

    def list_models(self) -> list[str]:
        try:
            response = self.client.get(self._url("/models"), headers=self._headers())
        except httpx.HTTPError as exc:
            raise self._network_error(exc) from exc
        if response.status_code != 200:
            raise self._error_from_response(response)
        data = response.json()
        items = data.get("data", data.get("models", [])) if isinstance(data, dict) else data
        ids: list[str] = []
        for item in items or []:
            model_id = item.get("id") or item.get("name") if isinstance(item, dict) else item
            if model_id:
                ids.append(str(model_id).removeprefix("models/"))
        return sorted(set(ids))

    def _body(self, model, messages, system, max_tokens, include_usage) -> dict:
        msgs = [{"role": "system", "content": system}] if system else []
        msgs += [{"role": m.role, "content": m.content} for m in messages]
        body: dict = {"model": model, "messages": msgs, "stream": True}
        # OpenAI's newer models require max_completion_tokens; others use max_tokens.
        body["max_completion_tokens" if self.spec.id == "openai" else "max_tokens"] = max_tokens
        if include_usage:
            body["stream_options"] = {"include_usage": True}
        return body

    def stream(
        self,
        model: str,
        messages: list[Message],
        system: str = "",
        max_tokens: int = 4096,
    ) -> Iterator[StreamEvent]:
        include_usage = True
        for _attempt in range(2):
            body = self._body(model, messages, system, max_tokens, include_usage)
            try:
                with self.client.stream(
                    "POST", self._url("/chat/completions"), json=body, headers=self._headers()
                ) as response:
                    if response.status_code == 400 and include_usage:
                        response.read()
                        if "stream_options" in response.text or "include_usage" in response.text:
                            include_usage = False  # provider does not support it; retry
                            continue
                        raise self._error_from_response(response)
                    if response.status_code != 200:
                        raise self._error_from_response(response)
                    yield from self._parse(response)
                    return
            except httpx.HTTPError as exc:
                raise self._network_error(exc) from exc

    def _parse(self, response: httpx.Response) -> Iterator[StreamEvent]:
        for data in iter_sse_data(response):
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("error"):
                err = obj["error"]
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                raise ProviderError(f"{self.spec.name}: {msg}")
            for choice in obj.get("choices") or []:
                delta = choice.get("delta") or {}
                text = delta.get("content")
                if text:
                    yield StreamEvent(text=text)
            usage = obj.get("usage")
            if isinstance(usage, dict):
                yield StreamEvent(
                    usage=Usage(
                        input_tokens=int(usage.get("prompt_tokens") or 0),
                        output_tokens=int(usage.get("completion_tokens") or 0),
                    )
                )
