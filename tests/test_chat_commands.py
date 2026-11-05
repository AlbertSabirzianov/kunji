"""Tests verifying chat slash commands registry and documentation alignment."""

import re
from pathlib import Path

from kunji.chat import ChatSession
from kunji.config import Config
from kunji.ui.input import SLASH_COMMANDS


def test_command_registry_exposed_and_valid():
    """Verify ChatSession exposes its registered commands without duplication."""
    commands = ChatSession.registered_commands()
    assert commands, "No commands registered in ChatSession"
    for cmd in commands:
        assert cmd.startswith("/"), f"Command {cmd} should start with '/'"
    # Verify exit commands and command handlers are accounted for
    for exit_cmd in ChatSession.EXIT_COMMANDS:
        assert exit_cmd in commands
    for handler_cmd in ChatSession.COMMAND_HANDLERS:
        assert handler_cmd in commands


def test_every_command_in_help_output(console_at):
    """Verify every registered command appears in the /help output and SLASH_COMMANDS."""
    commands = ChatSession.registered_commands()
    console = console_at(120)
    cfg = Config.load()
    cfg.set("default_model", "ollama:llama")
    session = ChatSession(cfg)
    session.cmd_help("")
    help_output = console.export_text(styles=False, clear=False)

    for cmd in commands:
        # Match the command token ensuring boundaries so aliases like /q match accurately
        pattern = rf"(?<![a-zA-Z0-9_-]){re.escape(cmd)}(?![a-zA-Z0-9_-])"
        assert re.search(pattern, help_output), (
            f"Registered command {cmd} missing from /help output"
        )
        assert cmd in SLASH_COMMANDS, f"Registered command {cmd} missing from SLASH_COMMANDS"


def test_every_command_in_readme_in_chat_table():
    """Verify every registered command appears in the README.md 'In chat' table."""
    commands = ChatSession.registered_commands()
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    assert "### In chat" in readme_text, "Missing '### In chat' section in README.md"
    in_chat_section = readme_text.split("### In chat", 1)[1].split("\n## ", 1)[0]

    for cmd in commands:
        pattern = rf"(?<![a-zA-Z0-9_-]){re.escape(cmd)}(?![a-zA-Z0-9_-])"
        assert re.search(pattern, in_chat_section), (
            f"Registered command {cmd} missing from README.md 'In chat' table"
        )


def test_aliases_behavior():
    """Verify command aliases map to expected behavior."""
    cfg = Config.load()
    cfg.set("default_model", "ollama:llama")
    session = ChatSession(cfg)

    # Exit aliases
    for cmd in ("/exit", "/quit", "/q"):
        assert session.command(cmd) == "exit"

    # Clear / new aliases map to same handler
    assert ChatSession.COMMAND_HANDLERS["/clear"] == ChatSession.COMMAND_HANDLERS["/new"]
