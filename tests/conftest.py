import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from rich.console import Console

from kunji.ui import set_console
from kunji.ui.theme import THEME


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self.store:
            raise PasswordDeleteError("missing")
        del self.store[(service, username)]


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Every test gets its own config/data/cache dirs and an in-memory keychain."""
    monkeypatch.setenv("KUNJI_HOME", str(tmp_path / "home"))
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "GROQ_API_KEY", "OPENROUTER_API_KEY", "KUNJI_DEV", "KUNJI_DEV_PUBLIC_KEY"):
        monkeypatch.delenv(var, raising=False)
    backend = MemoryKeyring()
    previous = keyring.get_keyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture
def console_at():
    def make(width: int) -> Console:
        console = Console(theme=THEME, width=width, record=True, force_terminal=True,
                          color_system="truecolor", height=40)
        set_console(console)
        return console

    return make
