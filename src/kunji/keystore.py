"""API key storage.

Keys are stored only in the operating system's credential store (Windows Credential
Manager, macOS Keychain, Secret Service on Linux) or read from environment variables.
Kunji never writes keys to its config file and never sends them anywhere except the
provider's own API.
"""

from __future__ import annotations

import os

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from kunji.constants import KEYRING_SERVICE


class KeyStoreError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


_FRIENDLY_BACKENDS = {
    "WinVaultKeyring": "Windows Credential Manager",
    "Keyring": "macOS Keychain",  # keyring.backends.macOS.Keyring
    "SecretServiceKeyring": "Secret Service (GNOME Keyring / KWallet)",
    "DBusKeyring": "KWallet",
    "LibSecretKeyring": "libsecret",
}


def backend_name() -> str:
    kr = keyring.get_keyring()
    cls = type(kr)
    if cls.__module__.endswith("fail"):
        return "none available"
    if cls.__name__ == "Keyring" and "macOS" not in cls.__module__:
        return cls.__module__.rsplit(".", 1)[-1]
    return _FRIENDLY_BACKENDS.get(cls.__name__, cls.__name__)


def backend_available() -> bool:
    return not type(keyring.get_keyring()).__module__.endswith("fail")


def env_names(provider_id: str, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    return (*extra, f"KUNJI_{provider_id.upper().replace('-', '_')}_API_KEY")


def get_key(provider_id: str, extra_env: tuple[str, ...] = ()) -> tuple[str | None, str]:
    """Return (key, source). Environment variables win so CI and scripts stay simple."""
    for name in env_names(provider_id, extra_env):
        value = os.environ.get(name)
        if value:
            return value.strip(), f"env:{name}"
    if not backend_available():
        return None, "none"
    try:
        value = keyring.get_password(KEYRING_SERVICE, provider_id)
    except KeyringError:
        return None, "none"
    return (value, "keychain") if value else (None, "none")


def set_key(provider_id: str, value: str) -> None:
    value = value.strip()
    if not value:
        raise KeyStoreError("The API key is empty.")
    if not backend_available():
        raise KeyStoreError(
            "No secure OS keychain is available on this system.",
            hint=f"Set an environment variable instead, e.g. "
            f"{env_names(provider_id)[-1]}=... (Linux: install gnome-keyring or KWallet).",
        )
    try:
        keyring.set_password(KEYRING_SERVICE, provider_id, value)
    except KeyringError as exc:
        raise KeyStoreError(f"Could not save the key to the keychain: {exc}") from exc


def delete_key(provider_id: str) -> bool:
    if not backend_available():
        return False
    try:
        keyring.delete_password(KEYRING_SERVICE, provider_id)
        return True
    except PasswordDeleteError:
        return False
    except KeyringError as exc:
        raise KeyStoreError(f"Could not delete the key: {exc}") from exc


def mask(value: str | None) -> str:
    if not value:
        return "—"
    if len(value) < 12:
        return "•" * 8
    return f"{value[:6]}{'•' * 8}{value[-4:]}"


def redact(text: str, *secrets: str | None) -> str:
    """Remove secrets from any text before it is shown or logged."""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, mask(secret))
    return text
