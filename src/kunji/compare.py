"""Send one prompt to several models at once and compare speed, cost and answers."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from kunji.catalog import Catalog, fmt_money, refresh_in_background
from kunji.config import Config
from kunji.engine import TurnResult, stream_turn
from kunji.providers import Message, ProviderError, resolve_ref
from kunji.providers.registry import all_specs, key_for
from kunji.ui import Card, Frame, answer, fmt_elapsed, get_console, hint


@dataclass
class Lane:
    ref: str
    started: float = field(default_factory=time.monotonic)
    chars: int = 0
    result: TurnResult | None = None
    error: str | None = None

    @property
    def done(self) -> bool:
        return self.result is not None or self.error is not None


class LanesView:
    def __init__(self, lanes: list[Lane]):
        self.lanes = lanes
        self.spinner = Spinner("dots", style="k.accent")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        for lane in self.lanes:
            grid = Table.grid(padding=(0, 1))
            grid.add_column(width=1, no_wrap=True)
            grid.add_column(overflow="ellipsis", no_wrap=True)
            if lane.result:
                r = lane.result
                info = f"{fmt_elapsed(r.elapsed)} · {r.usage.output_tokens:,} tok"
                grid.add_row(Text("✓", style="k.ok"),
                             Text.assemble(lane.ref, ("  " + info, "k.dim")))
            elif lane.error:
                grid.add_row(Text("✗", style="k.err"),
                             Text.assemble(lane.ref, ("  " + lane.error, "k.err")))
            else:
                elapsed = fmt_elapsed(time.monotonic() - lane.started)
                grid.add_row(self.spinner, Text.assemble(lane.ref, (f"  {elapsed}", "k.dim")))
            yield grid


def default_refs(cfg: Config, limit: int = 3) -> list[str]:
    refs = []
    default = str(cfg.get("default_model") or "")
    if default:
        refs.append(default)
    for pid, spec in all_specs(cfg).items():
        model = cfg.provider_entry(pid).get("default_model")
        if not model or (spec.needs_key and not key_for(spec)[0]):
            continue
        refs.append(f"{pid}:{model}")
    return list(dict.fromkeys(refs))[:limit]


def run_compare(cfg: Config, prompt: str, refs: list[str]) -> list[Lane]:
    console = get_console()
    refresh_in_background(cfg)
    catalog = Catalog(cfg)
    lanes = [Lane(ref) for ref in refs]
    messages = [Message("user", prompt)]

    def work(lane: Lane) -> None:
        try:
            spec, model = resolve_ref(cfg, lane.ref)
            lane.result = stream_turn(cfg, spec, model, messages, catalog=catalog,
                                      on_text=lambda t: setattr(lane, "chars", lane.chars + len(t)))
        except ProviderError as exc:
            lane.error = exc.message
        except Exception as exc:  # noqa: BLE001 - one lane failing must not break the others
            lane.error = str(exc) or type(exc).__name__

    threads = [threading.Thread(target=work, args=(lane,), daemon=True) for lane in lanes]
    with Live(LanesView(lanes), console=console, refresh_per_second=12, transient=False):
        for t in threads:
            t.start()
        while not all(lane.done for lane in lanes):
            time.sleep(0.05)
    console.print()

    for lane in lanes:
        if lane.result and lane.result.text:
            r = lane.result
            console.print(Frame(answer(r.text), title=lane.ref))
            approx = "~" if r.usage.estimated else ""
            console.print(Text(
                f"  {fmt_elapsed(r.elapsed)} · {approx}{r.usage.input_tokens:,} in · "
                f"{approx}{r.usage.output_tokens:,} out · {fmt_money(cfg, r.cost_usd)}",
                style="k.dim"))
            console.print()

    ok = [lane.result for lane in lanes if lane.result]
    if len(ok) >= 2:
        fastest = min(ok, key=lambda r: r.elapsed)
        priced = [r for r in ok if r.cost_usd is not None]
        rows = [("Fastest", f"{fastest.ref}  ·  {fmt_elapsed(fastest.elapsed)}")]
        if priced:
            cheapest = min(priced, key=lambda r: r.cost_usd or 0)
            rows.append(("Cheapest", f"{cheapest.ref}  ·  {fmt_money(cfg, cheapest.cost_usd)}"))
        longest = max(ok, key=lambda r: r.usage.output_tokens)
        rows.append(("Longest", f"{longest.ref}  ·  {longest.usage.output_tokens:,} tokens"))
        console.print(Card(rows, title="Compare"))
    elif not ok:
        hint("  No model answered. Check keys with: kunji keys test")
    return lanes
