"""Responsive building blocks.

Every component measures the terminal at render time (`options.max_width`), so
anything inside a Live view re-flows instantly when the window is resized, and
static output always fits the width the terminal had when it was printed.
Content is capped at `display.max_width` columns so it stays readable on very
wide screens.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rich import box
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.segment import Segment
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from kunji.ui.theme import get_console, get_err_console

DEFAULT_MAX_WIDTH = 100
NARROW = 56

_max_width = DEFAULT_MAX_WIDTH


def set_max_width(value: int) -> None:
    global _max_width
    _max_width = max(40, int(value))


def fit(options: ConsoleOptions, cap: int | None = None) -> int:
    return max(20, min(options.max_width, cap or _max_width))


class Capped:
    """Render a child no wider than the cap (but never wider than the terminal)."""

    def __init__(self, renderable: RenderableType, cap: int | None = None):
        self.renderable = renderable
        self.cap = cap

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from console.render(self.renderable, options.update(width=fit(options, self.cap)))


def chip(label: str) -> Text:
    return Text(f" {label} ", style="k.chip")


_STATUS_STYLES = {
    "k.ok": {"ACTIVE", "RUNNING", "OK", "READY", "KEY SET", "LOCAL", "ENV", "PASS", "DONE"},
    "k.warn": {"WARN", "RATE LIMITED", "NEAR LIMIT", "UPDATE", "SKIPPED", "UNVERIFIED"},
    "k.err": {"ERROR", "FAILED", "MISSING", "BLOCKED", "INVALID", "FAIL", "OFFLINE"},
}


def status_text(value: str) -> Text:
    upper = value.upper()
    for style, words in _STATUS_STYLES.items():
        if upper in words:
            return Text(value, style=style)
    return Text(value)


def _as_text(value: Any) -> Text:
    if isinstance(value, Text):
        return value
    return Text(str(value))


class Card:
    """Key/value card. Two columns when wide, stacked label/value when narrow."""

    def __init__(
        self,
        rows: Sequence[tuple[str, Any]],
        title: str | None = None,
        footer: RenderableType | None = None,
        cap: int | None = None,
    ):
        self.rows = rows
        self.title = title
        self.footer = footer
        self.cap = cap

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = fit(options, self.cap)
        narrow = width < NARROW
        parts: list[RenderableType] = []
        if self.title:
            parts += [chip(self.title), Text("")]
        if narrow:
            for i, (label, value) in enumerate(self.rows):
                if i:
                    parts.append(Text(""))
                parts.append(Text(label, style="k.label"))
                parts.append(_as_text(value))
        else:
            label_w = min(18, max((len(k) for k, _ in self.rows), default=8) + 2)
            grid = Table.grid(padding=(0, 2))
            grid.add_column(style="k.label", width=label_w, no_wrap=True)
            grid.add_column(overflow="fold")
            for label, value in self.rows:
                grid.add_row(label, _as_text(value))
            parts.append(grid)
        if self.footer is not None:
            parts += [Text(""), self.footer]
        yield Panel(
            Group(*parts),
            box=box.SQUARE,
            border_style="k.border",
            padding=(0, 1) if narrow else (1, 2),
            width=width,
        )


class Frame:
    """A thin square border around anything, with an optional chip title."""

    def __init__(
        self, renderable: RenderableType, title: str | None = None, cap: int | None = None
    ):
        self.renderable = renderable
        self.title = title
        self.cap = cap

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = fit(options, self.cap)
        narrow = width < NARROW
        body: RenderableType = self.renderable
        if self.title:
            body = Group(chip(self.title), Text(""), self.renderable)
        yield Panel(
            body,
            box=box.SQUARE,
            border_style="k.border",
            padding=(0, 1) if narrow else (1, 2),
            width=width,
        )


@dataclass
class Column:
    header: str
    priority: int = 0  # 0 = always shown; higher numbers are hidden first on narrow screens
    min_width: int = 6
    justify: str = "left"
    ratio: int | None = None
    style: str | None = None


class ResponsiveTable:
    """Daytona-style list: header rule, no grid lines, optional highlighted row."""

    def __init__(
        self,
        columns: Sequence[Column],
        rows: Sequence[Sequence[Any]],
        selected: int | None = None,
        title: str | None = None,
        empty: str = "Nothing here yet.",
        cap: int | None = None,
        compact: bool = False,
    ):
        self.columns = list(columns)
        self.rows = rows
        self.selected = selected
        self.title = title
        self.empty = empty
        self.cap = cap
        self.compact = compact  # title in the border, no blank padding lines

    def natural_widths(self) -> list[int]:
        widths = []
        for i, col in enumerate(self.columns):
            longest = max((len(_as_text(r[i]).plain) for r in self.rows if i < len(r)), default=0)
            widths.append(min(max(len(col.header), longest, 1), 48))
        return widths

    def visible_columns(self, width: int) -> list[int]:
        pad = 2 if width >= NARROW else 1
        budget = width - 4
        natural = self.natural_widths()
        need = [
            (min(self.columns[i].min_width, natural[i]) if self.columns[i].ratio else natural[i])
            + pad * 2
            for i in range(len(self.columns))
        ]
        order = sorted(range(len(self.columns)), key=lambda i: (self.columns[i].priority, i))
        chosen: list[int] = []
        used = 0
        for i in order:
            if chosen and used + need[i] > budget:
                continue
            chosen.append(i)
            used += need[i]
        return sorted(chosen)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = fit(options, self.cap)
        narrow = width < NARROW
        if not self.rows:
            yield Frame(Text(self.empty, style="k.dim"), title=self.title, cap=self.cap)
            return
        cols = self.visible_columns(width)
        natural = self.natural_widths()
        table = Table(
            box=box.SIMPLE_HEAD,
            show_edge=False,
            header_style="k.dim",
            border_style="k.border",
            padding=(0, 1 if narrow else 2),
            expand=True,
        )
        for i in cols:
            c = self.columns[i]
            min_w = min(c.min_width, natural[i]) if c.ratio else natural[i]
            table.add_column(
                c.header,
                justify=c.justify,
                no_wrap=True,
                overflow="ellipsis",
                min_width=min(min_w, width // 2),
                ratio=c.ratio,
                style=c.style,
            )
        for r, row in enumerate(self.rows):
            cells = [row[i] if i < len(row) else "" for i in cols]
            if r == self.selected:
                table.add_row(
                    *[c.plain if isinstance(c, Text) else str(c) for c in cells], style="k.selected"
                )
            else:
                table.add_row(*[_as_text(c) for c in cells])
        if self.compact:
            yield Panel(
                table,
                box=box.SQUARE,
                border_style="k.border",
                padding=(0, 0),
                width=width,
                title=chip(self.title) if self.title else None,
                title_align="left",
            )
            return
        body: RenderableType = table
        if self.title:
            body = Group(chip(self.title), Text(""), table)
        yield Panel(
            body,
            box=box.SQUARE,
            border_style="k.border",
            padding=(0, 0) if narrow else (1, 1),
            width=width,
        )


class Strip:
    """One-row summary: labels as column headers, values underneath.

    Takes 5 lines instead of a tall card. On narrow terminals the lowest-priority
    columns are hidden first (priority 0 = always shown).

        Strip([("Provider", "Anthropic"), ("Model", "claude-sonnet"), ("State", ok, 0)],
              title="kunji chat")
    """

    def __init__(self, items: Sequence[tuple], title: str | None = None, cap: int | None = None):
        self.items = list(items)
        self.title = title
        self.cap = cap

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        columns, values = [], []
        for index, item in enumerate(self.items):
            label, value = item[0], item[1]
            priority = item[2] if len(item) > 2 else index
            columns.append(Column(label, priority=priority, min_width=4))
            values.append(value)
        yield ResponsiveTable(columns, [values], title=self.title, cap=self.cap, compact=True)


def fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs:02d}s"


class Steps:
    """Live step list: a spinner while a step runs, then ✓ or ✗ with its duration.

    with Steps() as steps:
        models = steps.run("Verifying key", provider.list_models)
    """

    def __init__(self, console: Console | None = None):
        self.console = console or get_console()
        self.lines: list[Text] = []
        self.current: str | None = None
        self.started = 0.0
        self.spinner = Spinner("dots", style="k.accent")
        self.live: Live | None = None

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from self.lines
        if self.current:
            grid = Table.grid(padding=(0, 1))
            grid.add_column(width=1, no_wrap=True)
            grid.add_column()
            grid.add_row(
                self.spinner,
                Text.assemble(
                    self.current, ("  " + fmt_elapsed(time.monotonic() - self.started), "k.dim")
                ),
            )
            yield grid

    def __enter__(self) -> Steps:
        self.live = Live(self, console=self.console, refresh_per_second=12, transient=False)
        self.live.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        self.current = None
        if self.live:
            self.live.refresh()
            self.live.__exit__(*exc)
            if not self.console.is_terminal and self.lines:
                self.console.print()  # non-terminal Live output ends without a newline

    def _finish(self, label: str, ok: bool, note: str = "", style: str | None = None) -> None:
        elapsed = time.monotonic() - self.started
        mark, mark_style = ("✓", "k.ok") if ok else ("✗", "k.err")
        if style:
            mark_style = style
            mark = "!"
        line = Text.assemble(
            (f"{mark} ", mark_style), label, ("  " + fmt_elapsed(elapsed), "k.dim")
        )
        if note:
            line.append(f"  {note}", style="k.dim" if ok else mark_style)
        self.lines.append(line)
        self.current = None
        if self.live:
            self.live.refresh()

    def run(
        self, label: str, fn: Callable[..., Any], *args: Any, done: str = "", **kwargs: Any
    ) -> Any:
        self.current = label
        self.started = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            self._finish(label, ok=False, note=_short(exc))
            raise
        note = done(result) if callable(done) else done
        self._finish(label, ok=True, note=note)
        return result

    def warn(self, label: str, note: str = "") -> None:
        self.started = time.monotonic()
        self._finish(label, ok=False, note=note, style="k.warn")

    def ok(self, label: str, note: str = "") -> None:
        self.started = time.monotonic()
        self._finish(label, ok=True, note=note)


def _short(exc: Exception, limit: int = 90) -> str:
    text = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Tail:
    """Render only the last lines that fit on screen (keeps live streaming smooth)."""

    def __init__(self, renderable: RenderableType, reserve: int = 2):
        self.renderable = renderable
        self.reserve = reserve

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        height = max(3, console.size.height - self.reserve)
        lines = console.render_lines(self.renderable, options.update(height=None), pad=False)
        for line in lines[-height:]:
            yield from line
            yield Segment.line()


class StreamView:
    """What you see while a model is answering."""

    def __init__(self, label: str = "Thinking"):
        self.text = ""
        self.label = label
        self.started = time.monotonic()
        self.spinner = Spinner("dots", style="k.accent")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if not self.text:
            grid = Table.grid(padding=(0, 1))
            grid.add_column(width=1, no_wrap=True)
            grid.add_column()
            grid.add_row(
                self.spinner,
                Text.assemble(
                    (f"{self.label}… {fmt_elapsed(time.monotonic() - self.started)}", "k.dim"),
                    ("   ctrl+c to stop", "k.dim"),
                ),
            )
            yield grid
            return
        yield Tail(Capped(answer(self.text)))


def answer(markdown_text: str) -> RenderableType:
    return Padding(Markdown(markdown_text, code_theme="monokai"), (0, 0, 0, 2))


# One-line messages ------------------------------------------------------------


def success(message: str, note: str = "") -> None:
    line = Text.assemble(("✓ ", "k.ok"), message)
    if note:
        line.append(f"  {note}", style="k.dim")
    get_console().print(line)


def warn(message: str, hint: str = "") -> None:
    get_err_console().print(Text.assemble(("! ", "k.warn"), (message, "k.warn")))
    if hint:
        get_err_console().print(Text("  " + hint, style="k.dim"))


def error(message: str, hint: str = "") -> None:
    get_err_console().print(Text.assemble(("✗ ", "k.err"), (message, "k.err")))
    if hint:
        get_err_console().print(Text("  " + hint, style="k.dim"))


def hint(message: str) -> None:
    """Dim helper line; leading spaces become a hanging indent so wrapping stays aligned."""
    stripped = message.lstrip(" ")
    indent = len(message) - len(stripped)
    get_console().print(Capped(Padding(Text(stripped, style="k.dim"), (0, 0, 0, indent))))


def keys_line(pairs: Sequence[tuple[str, str]]) -> Text:
    """e.g.  enter send · alt+enter newline · ctrl+c stop"""
    text = Text()
    for i, (key, label) in enumerate(pairs):
        if i:
            text.append("  ·  ", style="k.dim")
        text.append(key)
        text.append(f" {label}", style="k.dim")
    return text


def form(
    title: str, fields: Sequence[tuple[str, str]], subtitle: str = "", active: int | None = 0
) -> Frame:
    """Read-only form view (used to review values before saving)."""
    parts: list[RenderableType] = []
    if subtitle:
        parts += [Text(subtitle, style="k.dim"), Text("═══", style="k.dim"), Text("")]
    for i, (label, value) in enumerate(fields):
        bar = Text("│ ", style="k.accent" if i == active else "k.border")
        parts.append(Text.assemble(bar, label))
        parts.append(Text.assemble(bar.copy(), ("> ", "k.accent"), value))
        parts.append(Text(""))
    if parts and parts[-1].plain == "":
        parts.pop()
    return Frame(Group(*parts), title=title)
