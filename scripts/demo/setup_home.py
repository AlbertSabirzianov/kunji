"""Create a throwaway KUNJI_HOME whose providers all point at the mock server."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PORT = 8765
CONFIG = f"""default_model = "anthropic:claude-sonnet-4-5"

[chat]
history = true

[display]
currency = "USD"

[budget.daily]
all = 2

[updates]
check = false

[network]
catalog = false

[cloud]
url = ""

[providers.anthropic]
default_model = "claude-sonnet-4-5"
base_url = "http://127.0.0.1:{PORT}"
added = "2026-11-01T10:00:00+00:00"

[providers.openai]
default_model = "gpt-4o-mini"
base_url = "http://127.0.0.1:{PORT}/v1"
added = "2026-11-01T10:00:00+00:00"

[providers.groq]
default_model = "llama-3.3-70b-versatile"
base_url = "http://127.0.0.1:{PORT}/v1"
added = "2026-11-01T10:00:00+00:00"

[providers.gemini]
default_model = "gemini-2.5-flash"
base_url = "http://127.0.0.1:{PORT}/v1"
added = "2026-11-01T10:00:00+00:00"

[pricing."anthropic:claude-sonnet-4-5"]
input = 3.0
output = 15.0

[pricing."openai:gpt-4o-mini"]
input = 0.15
output = 0.60

[pricing."groq:llama-3.3-70b-versatile"]
input = 0.59
output = 0.79

[pricing."gemini:gemini-2.5-flash"]
input = 0.30
output = 2.50
"""


def make(home: Path) -> None:
    if home.exists():
        shutil.rmtree(home)
    (home / "config").mkdir(parents=True)
    (home / "config" / "config.toml").write_text(CONFIG, encoding="utf-8")


if __name__ == "__main__":
    make(Path(sys.argv[1]))
