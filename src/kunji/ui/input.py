"""Interactive input: chat prompt (prompt_toolkit) and pickers (questionary)."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable

import questionary
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from kunji.ui.theme import ACCENT, BORDER, CHIP_BG, CHIP_FG, DIM

SLASH_COMMANDS: dict[str, str] = {
    "/help": "Show commands and shortcuts",
    "/model": "Switch model, e.g. /model groq:llama-3.3-70b-versatile",
    "/models": "List models of the current provider (/models <filter>)",
    "/system": "Show or set the system prompt",
    "/cost": "Cost of this session and today",
    "/file": "Attach a text file to your next message (/file clear to remove)",
    "/prompts": "List saved prompts; use one with @name <text>",
    "/history": "Recent saved chats (/history <text> to search)",
    "/retry": "Regenerate the last answer",
    "/new": "Start a new conversation",
    "/save": "Export the conversation as a markdown file",
    "/exit": "Leave the chat (back to the menu if you came from it)",
}

PROMPT_STYLE = Style.from_dict(
    {
        "prompt": f"{ACCENT} bold",
        "continuation": DIM,
        "bottom-toolbar": f"noreverse {DIM}",
        "bottom-toolbar.text": f"noreverse {DIM}",
        "completion-menu": "bg:#1e1e1e #e6e6e6",
        "completion-menu.completion": "bg:#1e1e1e #e6e6e6",
        "completion-menu.completion.current": f"bg:{CHIP_BG} {CHIP_FG}",
        "completion-menu.meta.completion": f"bg:#1e1e1e {DIM}",
        "completion-menu.meta.completion.current": f"bg:#cfcfcf {CHIP_FG}",
        "scrollbar.background": "bg:#2a2a2a",
        "scrollbar.button": f"bg:{BORDER}",
    }
)

PICKER_STYLE = questionary.Style(
    [
        ("qmark", f"fg:{ACCENT} bold"),
        ("question", "bold"),
        ("pointer", f"fg:{ACCENT} bold"),
        ("highlighted", f"fg:{CHIP_FG} bg:{CHIP_BG}"),
        ("selected", f"fg:{ACCENT}"),
        ("answer", f"fg:{ACCENT} bold"),
        ("instruction", f"fg:{DIM}"),
        ("text", ""),
        ("disabled", f"fg:{DIM} italic"),
    ]
)


class SlashCompleter(Completer):
    def __init__(self, model_refs: Callable[[], Iterable[str]],
                 prompt_names: Callable[[], Iterable[str]] | None = None):
        self.model_refs = model_refs
        self.prompt_names = prompt_names or (lambda: [])
        self.paths = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if "\n" in text:
            return
        if text.startswith("@") and " " not in text:
            for name in self.prompt_names():
                if name.startswith(text[1:].lower()):
                    yield Completion(f"@{name}", start_position=-len(text))
            return
        if text.startswith("/file ") and text[6:] != "clear":
            sub = Document(text[6:], len(text) - 6)
            yield from self.paths.get_completions(sub, complete_event)
            return
        if not text.startswith("/"):
            return
        if " " not in text:
            for cmd, desc in SLASH_COMMANDS.items():
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text), display_meta=desc)
            return
        if text.startswith("/model "):
            arg = text[len("/model "):]
            for ref in self.model_refs():
                if arg.lower() in ref.lower():
                    yield Completion(ref, start_position=-len(arg))


def _bindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add("enter")
    def _submit(event):
        buf = event.current_buffer
        state = buf.complete_state
        if state and state.current_completion:
            buf.apply_completion(state.current_completion)
            return
        buf.validate_and_handle()

    @kb.add("escape", "enter")  # alt+enter / option+enter
    def _newline(event):
        event.current_buffer.insert_text("\n")

    @kb.add("c-j")  # ctrl+j also inserts a newline (works in every terminal)
    def _newline2(event):
        event.current_buffer.insert_text("\n")

    return kb


def chat_prompt(history_file: str | None, model_refs: Callable[[], Iterable[str]],
                toolbar: Callable[[], str],
                prompt_names: Callable[[], Iterable[str]] | None = None) -> PromptSession:
    try:
        history = FileHistory(history_file) if history_file else InMemoryHistory()
    except OSError:
        history = InMemoryHistory()
    return PromptSession(
        history=history,
        completer=SlashCompleter(model_refs, prompt_names),
        complete_while_typing=True,
        key_bindings=_bindings(),
        multiline=True,
        style=PROMPT_STYLE,
        bottom_toolbar=lambda: [("class:bottom-toolbar.text", toolbar())],
        prompt_continuation=lambda width, line_number, is_soft_wrap: [
            ("class:continuation", "  ")
        ],
        reserve_space_for_menu=6,
    )


PROMPT_MESSAGE = [("class:prompt", "› ")]


def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def pick(message: str, choices: list, default=None):
    return questionary.select(
        message, choices=choices, default=default, style=PICKER_STYLE, qmark="◆",
        pointer="❯", instruction="(↑/↓, enter)",
    ).ask()


def pick_or_type(message: str, choices: list[str], default: str = "") -> str | None:
    if not choices:
        return questionary.text(message, default=default, style=PICKER_STYLE, qmark="◆").ask()
    return questionary.autocomplete(
        message, choices=choices, default=default, style=PICKER_STYLE, qmark="◆",
        match_middle=True, validate=lambda v: bool(v.strip()) or "Type a model name",
    ).ask()


def secret(message: str) -> str | None:
    return questionary.password(message, style=PICKER_STYLE, qmark="◆").ask()


def confirm(message: str, default: bool = True) -> bool:
    answer = questionary.confirm(message, default=default, style=PICKER_STYLE, qmark="◆").ask()
    return bool(answer)
