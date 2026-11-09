"""Update notices and the (optional) cloud check-in.

What is sent, and only when enabled:
  * Update check -> GET https://pypi.org/pypi/kunji/json (nothing about you is sent).
  * Cloud check-in (only if `cloud.url` is set) -> POST {install_id, version, os,
    license_key?}. The install id is a random UUID, not tied to your hardware.

API keys and prompts are NEVER sent to kunji servers.

Server replies are signed with Ed25519. The client only trusts replies whose
signature matches a public key shipped in constants.CHECKIN_PUBLIC_KEYS, so a
cached reply cannot be edited by hand to unlock anything.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from kunji import __version__
from kunji.config import Config, atomic_write, cache_dir, data_dir
from kunji.constants import CACHE_TTL_SECONDS, CHECKIN_PUBLIC_KEYS, PYPI_JSON_URL

# Versions -----------------------------------------------------------------------


def parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value.split("+", 1)[0])[:4]
    return tuple(int(p) for p in parts) or (0,)


def is_newer(candidate: str, current: str = __version__) -> bool:
    return parse_version(candidate) > parse_version(current)


def _read_json(path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def cached_update_notice() -> str | None:
    blob = _read_json(cache_dir() / "update.json") or {}
    latest = blob.get("latest")
    if latest and is_newer(latest):
        return latest
    return None


def check_updates(cfg: Config, force: bool = False) -> str | None:
    if not cfg.get("updates.check", True):
        return None
    path = cache_dir() / "update.json"
    blob = _read_json(path) or {}
    if not force and time.time() - float(blob.get("fetched_at", 0)) < CACHE_TTL_SECONDS:
        return blob.get("latest") if blob.get("latest") and is_newer(blob["latest"]) else None
    try:
        with httpx.Client(timeout=4.0) as client:
            latest = client.get(PYPI_JSON_URL).json()["info"]["version"]
    except Exception:  # noqa: BLE001 - offline is fine
        return None
    try:
        atomic_write(path, json.dumps({"fetched_at": time.time(), "latest": latest}).encode())
    except OSError:
        pass
    return latest if is_newer(latest) else None


def check_updates_in_background(cfg: Config) -> threading.Thread:
    thread = threading.Thread(target=check_updates, args=(cfg,), daemon=True)
    thread.start()
    return thread


# Install id -------------------------------------------------------------------


def install_id() -> str:
    path = data_dir() / "install_id"
    try:
        value = path.read_text(encoding="utf-8").strip()
        uuid.UUID(value)
        return value
    except (OSError, ValueError):
        value = str(uuid.uuid4())
        try:
            atomic_write(path, value.encode())
        except OSError:
            pass
        return value


# Signed entitlements ----------------------------------------------------------


@dataclass
class Entitlement:
    plan: str = "free"
    features: list[str] = field(default_factory=list)
    trial_ends: str | None = None
    min_version: str | None = None
    latest_version: str | None = None
    message: str | None = None
    verified: bool = False

    @property
    def outdated(self) -> bool:
        return bool(self.min_version) and is_newer(self.min_version)


def _public_keys() -> list[str]:
    keys = list(CHECKIN_PUBLIC_KEYS)
    if os.environ.get("KUNJI_DEV") == "1" and os.environ.get("KUNJI_DEV_PUBLIC_KEY"):
        keys.append(os.environ["KUNJI_DEV_PUBLIC_KEY"])
    return keys


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_blob(blob: dict, expected_install_id: str, now: float | None = None) -> dict | None:
    """Return the payload dict if the signature is valid and not expired, else None."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        payload_bytes = _b64decode(blob["payload"])
        signature = _b64decode(blob["sig"])
    except (KeyError, TypeError, ValueError):
        return None
    for key in _public_keys():
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(key)).verify(
                signature, payload_bytes
            )
        except (InvalidSignature, ValueError):
            continue
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError:
            return None
        now = time.time() if now is None else now
        if payload.get("install_id") != expected_install_id:
            return None
        if float(payload.get("expires_at", 0)) < now:
            return None
        return payload
    return None


def _entitlement_from(payload: dict | None) -> Entitlement:
    if not payload:
        return Entitlement()
    return Entitlement(
        plan=str(payload.get("plan", "free")),
        features=list(payload.get("features") or []),
        trial_ends=payload.get("trial_ends"),
        min_version=payload.get("min_version"),
        latest_version=payload.get("latest_version"),
        message=payload.get("message"),
        verified=True,
    )


def _allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}


def load_entitlement() -> Entitlement:
    blob = _read_json(cache_dir() / "entitlement.json")
    if not blob:
        return Entitlement()
    return _entitlement_from(verify_blob(blob, install_id()))


def checkin(
    cfg: Config, license_key: str | None = None, transport: httpx.BaseTransport | None = None
) -> Entitlement:
    url = str(cfg.get("cloud.url") or "").rstrip("/")
    if not url or not cfg.get("cloud.checkin", True) or not _allowed_url(url):
        return load_entitlement()
    body = {
        "install_id": install_id(),
        "version": __version__,
        "os": platform.system().lower(),
    }
    if license_key:
        body["license_key"] = license_key
    try:
        with httpx.Client(timeout=5.0, transport=transport) as client:
            response = client.post(f"{url}/v1/checkin", json=body)
            response.raise_for_status()
            blob = response.json()
    except Exception:  # noqa: BLE001 - fall back to the cached, signed entitlement
        return load_entitlement()
    payload = verify_blob(blob, body["install_id"])
    if payload is None:
        return load_entitlement()
    try:
        atomic_write(cache_dir() / "entitlement.json", json.dumps(blob).encode())
    except OSError:
        pass
    return _entitlement_from(payload)
