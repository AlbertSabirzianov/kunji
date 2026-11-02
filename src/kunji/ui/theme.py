"""Kunji's visual language: monochrome + one accent, inspired by Daytona's CLI.

Every colour is an explicit hex value. Named ANSI colours like "white" or "black"
are remapped by terminal themes (Windows Terminal renders "white" as light grey),
which made labels unreadable — hex colours look the same everywhere.
"""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

ACCENT = "#3ddc84"
WARN = "#f5a35c"
ERROR = "#ff6b6b"
DIM = "#8b8b8b"
BORDER = "#4b4b4b"
CHIP_FG = "#0b0b0b"
CHIP_BG = "#ececec"
MUTED_BG = "#333333"
MUTED_FG = "#f0f0f0"

THEME = Theme(
    {
        "k.dim": DIM,
        "k.label": DIM,
        "k.accent": ACCENT,
        "k.ok": ACCENT,
        "k.warn": WARN,
        "k.err": ERROR,
        "k.border": BORDER,
        "k.title": "bold",
        "k.chip": f"bold {CHIP_FG} on {CHIP_BG}",
        "k.selected": f"{CHIP_FG} on {CHIP_BG}",
        "k.button": f"bold {CHIP_FG} on {ACCENT}",
        "k.button.muted": f"{MUTED_FG} on {MUTED_BG}",
        "k.code": f"{ACCENT}",
        "markdown.code": ACCENT,
        "markdown.link": ACCENT,
        "markdown.link_url": DIM,
        "markdown.block_quote": DIM,
        "markdown.hr": BORDER,
        "markdown.item.bullet": DIM,
        "markdown.item.number": DIM,
    }
)

_console: Console | None = None
_err_console: Console | None = None


def get_console() -> Console:
    global _console
    if _console is None:
        _console = Console(theme=THEME, highlight=False)
    return _console


def get_err_console() -> Console:
    global _err_console
    if _err_console is None:
        _err_console = Console(theme=THEME, highlight=False, stderr=True)
    return _err_console


def set_console(console: Console) -> None:
    """Used by tests to capture output at a fixed width."""
    global _console, _err_console
    _console = console
    _err_console = console
