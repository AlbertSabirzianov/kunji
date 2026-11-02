"""Provider interface shared by every AI backend."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

import httpx

from kunji import __version__
from kunji.keystore import redact


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    kind: str  # "openai" (OpenAI-compatible) or "anthropic"
    base_url: str
    env_vars: tuple[str, ...] = ()
    needs_key: bool = True
    key_url: str = ""
    openrouter_prefix: str | None = None  # used to look up prices
    custom: bool = False


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class StreamEvent:
    text: str | None = None
    usage: Usage | None = None


@dataclass
class ProviderError(Exception):
    message: str
    status: int | None = None
    retryable: bool = False
    hint: str = ""
    extra: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


class Provider(ABC):
    def __init__(
        self,
        spec: ProviderSpec,
        api_key: str | None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.spec = spec
        self.api_key = api_key
        self.client = httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            transport=transport,
            headers={"user-agent": f"kunji/{__version__}"},
            follow_redirects=False,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> Provider:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @abstractmethod
    def list_models(self) -> list[str]: ...

    @abstractmethod
    def stream(
        self,
        model: str,
        messages: list[Message],
        system: str = "",
        max_tokens: int = 4096,
    ) -> Iterator[StreamEvent]: ...

    # Helpers -----------------------------------------------------------------
    def _url(self, path: str) -> str:
        return self.spec.base_url.rstrip("/") + path

    def _error_from_response(self, response: httpx.Response) -> ProviderError:
        try:
            response.read()
            body_text = response.text
        except httpx.HTTPError:
            body_text = ""
        detail = _extract_error_message(body_text) or response.reason_phrase or "Request failed"
        detail = redact(detail, self.api_key)
        status = response.status_code
        name = self.spec.name
        if status in (401, 403):
            return ProviderError(
                f"{name} rejected the API key ({status}): {detail}",
                status=status,
                hint=f"Update it with: kunji keys add {self.spec.id}",
            )
        if status == 404:
            return ProviderError(
                f"{name}: not found ({detail})",
                status=status,
                hint=f"Check the model name with: kunji models {self.spec.id}",
            )
        if status == 429:
            return ProviderError(
                f"{name} rate limit or quota reached: {detail}",
                status=status,
                retryable=True,
                hint="Wait a moment, or set a fallback: kunji config set fallback '[\"groq:...\"]'",
            )
        if status >= 500:
            return ProviderError(
                f"{name} server error ({status}): {detail}", status=status, retryable=True
            )
        return ProviderError(f"{name} error ({status}): {detail}", status=status)

    def _network_error(self, exc: Exception) -> ProviderError:
        hint = ""
        if self.spec.id == "ollama":
            hint = "Is Ollama running? Start it with: ollama serve"
        detail = redact(str(exc), self.api_key) or type(exc).__name__
        return ProviderError(
            f"Could not reach {self.spec.name}: {detail}",
            retryable=True,
            hint=hint,
        )


def _extract_error_message(body: str) -> str:
    if not body:
        return ""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()[:300]
    if isinstance(data, list) and data:
        data = data[0]
    if isinstance(data, dict):
        err = data.get("error", data)
        if isinstance(err, dict):
            msg = err.get("message") or err.get("msg") or err.get("type")
            if msg:
                return str(msg)[:300]
        if isinstance(err, str):
            return err[:300]
        if "message" in data:
            return str(data["message"])[:300]
    return body.strip()[:300]


def iter_sse_data(response: httpx.Response) -> Iterator[str]:
    """Yield the payload of each `data:` line in a server-sent-events stream."""
    for raw in response.iter_lines():
        line = raw.strip()
        if not line or line.startswith(":"):
            continue
        if line.startswith("data:"):
            yield line[5:].strip()
