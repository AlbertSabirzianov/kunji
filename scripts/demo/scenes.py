"""Demo scenes for record.py. Each scene drives a real kunji session against mock_server.py."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

DOWN, UP, ENTER, CTRL_D, CTRL_C = "\x1b[B", "\x1b[A", "\r", "\x04", "\x03"


def shell(s, command: str) -> None:
    s.wait(r"\$ $")
    s.pause(0.6)
    s.type(command, cps=16)
    s.pause(0.4)
    s.send(ENTER)


def ask_in_chat(s, text: str, wait_for: str, hold: float = 1.6) -> None:
    s.type(text)
    s.pause(0.35)
    s.send(ENTER)
    s.wait(wait_for)
    s.pause(hold)


def demo(s) -> None:
    """menu → chat → /model switch → /cost (README hero, ~25 s)."""
    shell(s, "kunji")
    s.wait("What would you like to do")
    s.pause(1.2)
    for key in (DOWN, DOWN, DOWN, UP, UP, UP):     # show the arrow-key menu
        s.send(key)
        s.pause(0.32)
    s.pause(0.5)
    s.send(ENTER)                                  # Start a new chat
    s.wait("enter.*send")
    s.pause(1.0)
    ask_in_chat(s, "explain recursion in one line", r"\$0\.\d+ ·")
    ask_in_chat(s, "/model groq:llama-3.3-70b-versatile", "Switched", hold=1.0)
    ask_in_chat(s, "now write a haiku about API keys", r"[\d.]+s\s*$", hold=1.8)
    ask_in_chat(s, "/cost", r"(?i)total|session", hold=2.6)
    s.send(CTRL_D)
    s.wait("What would you like to do")
    s.pause(0.8)
    s.send(CTRL_C)
    s.wait("bye")
    s.pause(1.2)


def compare(s) -> None:
    """One prompt, three models, side by side."""
    shell(s, 'kunji compare "write a haiku about API keys" '
             "-m anthropic:claude-sonnet-4-5 -m groq:llama-3.3-70b-versatile "
             "-m gemini:gemini-2.5-flash")
    s.wait("cheapest|fastest")
    s.pause(3.5)


def commit(s) -> None:
    """kunji @commit writes a commit message from staged changes."""
    shell(s, "git diff --staged --stat")
    s.pause(1.2)
    shell(s, "kunji @commit")
    s.wait(r"[\d.]+s\s*$")
    s.pause(3.0)
    shell(s, 'git commit -qm "$(kunji @commit --raw)"')
    s.pause(1.5)
    shell(s, "git log -1 --format=%B")
    s.pause(3.5)


def budget(s) -> None:
    """Daily budget warning at 80%."""
    shell(s, "kunji chat")
    s.wait("enter.*send")
    s.pause(1.5)
    ask_in_chat(s, "give me a regex for email addresses", r"[\d.]+s\s*$", hold=2.0)
    ask_in_chat(s, "/cost", r"(?i)total|session", hold=3.0)
    s.send(CTRL_D)
    s.pause(1.0)
    shell(s, "kunji budget show")
    s.pause(3.5)


def setup_commit(home: Path, cwd: Path) -> None:
    """A tiny git repo with one staged change."""
    def git(*args):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
    git("init", "-q")
    git("config", "user.email", "demo@example.com")
    git("config", "user.name", "demo")
    (cwd / "chat.py").write_text("def reply(text):\n    return text\n")
    git("add", ".")
    git("commit", "-qm", "init")
    (cwd / "chat.py").write_text(
        "def reply(text, usage):\n    print(meta_line(usage))\n    return text\n\n\n"
        "def meta_line(usage):\n    return f\"{usage.model} · {usage.cost}\"\n")
    git("add", ".")


def setup_budget(home: Path, cwd: Path) -> None:
    """Pretend $1.64 of the $2.00 daily budget is already used (82%)."""
    ledger = home / "data" / "usage.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    rows = [("anthropic", "claude-sonnet-4-5", 1.12), ("openai", "gpt-4o-mini", 0.31),
            ("groq", "llama-3.3-70b-versatile", 0.21)]
    with ledger.open("w", encoding="utf-8") as fh:
        for i, (provider, model, cost) in enumerate(rows):
            fh.write(json.dumps({"ts": now - 600 * (i + 1), "provider": provider, "model": model,
                                 "in": 40000, "out": 9000, "cost": cost, "est": False}) + "\n")


SCENES = {
    "demo": {"cols": 92, "rows": 30, "run": demo},
    "compare": {"cols": 92, "rows": 34, "run": compare},
    "commit": {"cols": 92, "rows": 26, "run": commit, "setup": setup_commit},
    "budget": {"cols": 92, "rows": 30, "run": budget, "setup": setup_budget},
}
