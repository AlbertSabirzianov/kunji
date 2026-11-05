"""In-memory keyring backend so demos show "keychain" without touching a real one."""

from keyring.backend import KeyringBackend

DEMO = {"anthropic", "openai", "groq", "gemini"}


class Keyring(KeyringBackend):
    priority = 1
    _store: dict = {}

    def get_password(self, service, username):
        if (service, username) in self._store:
            return self._store[(service, username)]
        return "demo-not-a-real-key" if service == "kunji" and username in DEMO else None

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def delete_password(self, service, username):
        self._store.pop((service, username), None)
