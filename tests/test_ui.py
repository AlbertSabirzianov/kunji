"""Every component must fit any terminal width without overflowing."""

import pytest
from rich.text import Text

from kunji.ui import Card, Column, Frame, ResponsiveTable, form, set_max_width, status_text

WIDTHS = [30, 44, 60, 80, 120, 200]


def lines_of(console):
    return console.export_text(styles=False, clear=False).splitlines()


def assert_fits(console, width):
    for line in lines_of(console):
        assert len(line) <= width, f"overflow at {width}: {line!r}"


@pytest.mark.parametrize("width", WIDTHS)
def test_card_fits_and_keeps_content(console_at, width):
    set_max_width(100)
    console = console_at(width)
    console.print(Card([("Provider", "Anthropic"), ("Model", "claude-sonnet-4-5-20250929"),
                        ("State", status_text("ACTIVE"))], title="Provider added"))
    assert_fits(console, width)
    text = console.export_text(clear=False)
    assert "Provider added" in text and "ACTIVE" in text


def test_card_is_capped_on_wide_terminals(console_at):
    set_max_width(100)
    console = console_at(200)
    console.print(Card([("A", "b")]))
    assert max(len(line) for line in lines_of(console)) == 100


def test_card_stacks_when_narrow(console_at):
    console = console_at(40)
    console.print(Card([("Provider", "Anthropic")]))
    text = lines_of(console)
    label_line = next(i for i, line in enumerate(text) if "Provider" in line)
    assert "Anthropic" not in text[label_line]
    assert "Anthropic" in text[label_line + 1]


@pytest.mark.parametrize("width", WIDTHS)
def test_table_hides_low_priority_columns(console_at, width):
    console = console_at(width)
    cols = [Column("Provider", min_width=9), Column("Key", priority=3, min_width=14),
            Column("Default model", priority=1, min_width=12, ratio=1),
            Column("Status", min_width=7)]
    rows = [["openai", "sk-123••••abcd", "gpt-4o-mini", status_text("KEY SET")],
            ["anthropic", "sk-ant••••3f9a", "claude-sonnet", status_text("KEY SET")]]
    console.print(ResponsiveTable(cols, rows, selected=1))
    assert_fits(console, width)
    text = console.export_text(clear=False)
    assert "openai" in text
    if width >= 80:
        assert "Key" in text


def test_selected_row_uses_explicit_hex_colors(console_at):
    console = console_at(80)
    console.print(ResponsiveTable([Column("A")], [["x"], [Text("y", style="k.ok")]], selected=1))
    html = console.export_html()
    assert "#ececec" in html  # chip/selected background is an explicit hex colour


@pytest.mark.parametrize("width", [30, 80])
def test_frame_and_form_fit(console_at, width):
    console = console_at(width)
    console.print(Frame(Text("hello " * 30), title="Session"))
    console.print(form("Add a new provider", [("Provider", "anthropic"),
                                              ("API key", "sk-ant••••3f9a")],
                       subtitle="Keys stay in your OS keychain"))
    assert_fits(console, width)


@pytest.mark.parametrize("width", WIDTHS)
def test_strip_is_five_lines_and_fits(console_at, width):
    from kunji.ui import Strip

    set_max_width(100)
    console = console_at(width)
    console.print(Strip([("Provider", "Anthropic", 2), ("Model", "claude-sonnet", 0),
                         ("Key", "keychain", 4), ("State", status_text("READY"), 1)],
                        title="kunji chat"))
    assert_fits(console, width)
    lines = lines_of(console)
    assert len(lines) == 5
    assert "claude-sonnet" in "\n".join(lines)
