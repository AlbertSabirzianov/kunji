"""Interactive chat session."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from rich.live import Live
from rich.text import Text

from kunji import checkin, usage
from kunji.catalog import Catalog, fmt_money, refresh_in_background
from kunji.config import Config, cache_dir, data_dir, ensure_dir
from kunji.engine import TurnResult, fallback_chain, stream_turn
from kunji.providers import Message, ProviderError, ProviderSpec, make_provider, resolve_ref
from kunji.providers.registry import all_specs, key_for
from kunji.ui import (
    Capped,
    Card,
    Column,
    ResponsiveTable,
    Steps,
    StreamView,
    answer,
    error,
    get_console,
    hint,
    keys_line,
    status_text,
    success,
    warn,
)
from kunji.ui.input import PROMPT_MESSAGE, SLASH_COMMANDS, chat_prompt


def meta_line(result: TurnResult, cfg: Config) -> Text:
    approx = "~" if result.usage.estimated else ""
    parts = [
        result.model,
        f"{approx}{result.usage.input_tokens:,} in",
        f"{approx}{result.usage.output_tokens:,} out",
        fmt_money(cfg, result.cost_usd),
        f"{result.elapsed:.1f}s",
    ]
    if result.interrupted:
        parts.append("stopped")
    return Text("  " + " · ".join(parts), style="k.dim")


def cached_models(provider_id: str) -> list[str]:
    try:
        return json.loads((cache_dir() / f"models_{provider_id}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return []


def save_models_cache(provider_id: str, models: list[str]) -> None:
    from kunji.config import atomic_write

    try:
        atomic_write(cache_dir() / f"models_{provider_id}.json", json.dumps(models).encode())
    except OSError:
        pass


def configured_refs(cfg: Config) -> list[str]:
    refs: list[str] = []
    for pid in all_specs(cfg):
        entry = cfg.provider_entry(pid)
        if entry.get("default_model"):
            refs.append(f"{pid}:{entry['default_model']}")
        refs += [f"{pid}:{m}" for m in cached_models(pid)[:200]]
    return list(dict.fromkeys(refs))


class ChatSession:
    def __init__(self, cfg: Config, model_ref: str | None = None, system: str | None = None):
        self.cfg = cfg
        self.console = get_console()
        self.spec, self.model = resolve_ref(cfg, model_ref)
        self.system = system if system is not None else str(cfg.get("chat.system_prompt") or "")
        self.messages: list[Message] = []
        self.session_cost = 0.0
        self.unpriced = 0
        self.turns = 0
        self.warned_budget: set[str] = set()
        refresh_in_background(cfg)
        checkin.check_updates_in_background(cfg)
        self.catalog = Catalog(cfg)

    # UI pieces ---------------------------------------------------------------
    @property
    def ref(self) -> str:
        return f"{self.spec.id}:{self.model}"

    def toolbar(self) -> str:
        today = fmt_money(self.cfg, usage.spent_today_usd())
        status = usage.check_budget(self.cfg, self.spec.id)
        budget = ""
        if status.state != "none":
            budget = f" / {fmt_money(self.cfg, None, display_amount=status.limit)}"
        return f" {self.ref}  ·  today {today}{budget}  ·  /help"

    def header(self) -> None:
        _, source = key_for(self.spec)
        status = usage.check_budget(self.cfg, self.spec.id)
        rows = [
            ("Provider", self.spec.name),
            ("Model", self.model),
            ("Key", "local, no key needed" if not self.spec.needs_key else
             ("OS keychain" if source == "keychain" else source.replace("env:", "env "))),
            ("State", status_text("READY")),
        ]
        if status.state != "none":
            rows.append(("Budget", f"{fmt_money(self.cfg, None, display_amount=status.spent)} / "
                         f"{fmt_money(self.cfg, None, display_amount=status.limit)} today"))
        self.console.print(Card(rows, title="kunji chat"))
        self.console.print(Capped(keys_line([
            ("enter", "send"), ("alt+enter", "newline"), ("/", "commands"), ("ctrl+d", "quit"),
        ])))
        self.console.print()

    # Main loop -----------------------------------------------------------------
    def run(self) -> None:
        self.header()
        history = ensure_dir(data_dir()) / "history.txt"
        session = chat_prompt(str(history), lambda: configured_refs(self.cfg), self.toolbar)
        while True:
            try:
                text = session.prompt(PROMPT_MESSAGE)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            text = text.strip()
            if not text:
                continue
            if text.startswith("/"):
                if self.command(text) == "exit":
                    break
                continue
            self.send(text)
        self.goodbye()

    def goodbye(self) -> None:
        spent = fmt_money(self.cfg, self.session_cost)
        self.console.print(Text(f"  {self.turns} replies · {spent} this session", style="k.dim"))
        latest = checkin.cached_update_notice()
        if latest:
            hint(f"  kunji {latest} is available — upgrade: pipx upgrade kunji")

    # Sending -------------------------------------------------------------------
    def budget_allows(self, spec: ProviderSpec) -> bool:
        status = usage.check_budget(self.cfg, spec.id)
        limit = fmt_money(self.cfg, None, display_amount=status.limit)
        spent = fmt_money(self.cfg, None, display_amount=status.spent)
        scope = "all providers" if status.scope == "all" else spec.name
        if status.state == "block":
            error(f"Daily budget reached for {scope}: {spent} / {limit}",
                  f"Raise it with: kunji budget set {status.scope} <amount>")
            return False
        if status.state == "warn" and status.scope not in self.warned_budget:
            self.warned_budget.add(status.scope)
            warn(f"80% of today's budget used for {scope}: {spent} / {limit}")
        return True

    def send(self, text: str, already_added: bool = False) -> None:
        if not self.budget_allows(self.spec):
            return
        if not already_added:
            self.messages.append(Message("user", text))
        result = self._answer_with_fallback()
        if result is None:
            self.messages.pop()
            hint("  Your message was not sent. Press ↑ to edit and try again.")
            return
        if result.text:
            self.messages.append(Message("assistant", result.text))
            self.console.print(Capped(answer(result.text)))
        self.console.print(meta_line(result, self.cfg))
        self.console.print()
        self.turns += 1
        if result.cost_usd is None:
            self.unpriced += 1
        else:
            self.session_cost += result.cost_usd

    def _answer_with_fallback(self) -> TurnResult | None:
        chain = fallback_chain(self.cfg, self.spec, self.model)
        for index, (spec, model) in enumerate(chain):
            view = StreamView()
            try:
                with Live(view, console=self.console, refresh_per_second=12, transient=True):
                    result = stream_turn(
                        self.cfg, spec, model, self.messages, self.system,
                        on_text=lambda t, v=view: setattr(v, "text", v.text + t),
                        catalog=self.catalog,
                    )
                return result
            except ProviderError as exc:
                last = index == len(chain) - 1
                if exc.retryable and not view.text and not last:
                    nxt = chain[index + 1]
                    warn(f"{exc.message}", f"Trying fallback {nxt[0].id}:{nxt[1]}")
                    continue
                error(exc.message, exc.hint)
                return None
        return None

    # Slash commands ------------------------------------------------------------
    def command(self, line: str) -> str | None:
        name, _, arg = line.partition(" ")
        arg = arg.strip()
        handler = {
            "/help": self.cmd_help,
            "/model": self.cmd_model,
            "/models": self.cmd_models,
            "/system": self.cmd_system,
            "/cost": self.cmd_cost,
            "/retry": self.cmd_retry,
            "/clear": self.cmd_clear,
            "/save": self.cmd_save,
        }.get(name)
        if name in ("/exit", "/quit", "/q"):
            return "exit"
        if handler is None:
            error(f"Unknown command {name}", "Type /help to see all commands")
            return None
        handler(arg)
        return None

    def cmd_help(self, _: str) -> None:
        rows = [[cmd, desc] for cmd, desc in SLASH_COMMANDS.items()]
        cols = [Column("Command", min_width=8), Column("What it does", min_width=12, ratio=1)]
        self.console.print(ResponsiveTable(cols, rows, title="Commands"))
        self.console.print(Capped(keys_line([
            ("enter", "send"), ("alt+enter / ctrl+j", "newline"), ("↑", "history"),
            ("ctrl+c", "stop reply"), ("ctrl+d", "quit"),
        ])))
        self.console.print()

    def cmd_model(self, arg: str) -> None:
        if not arg:
            refs = configured_refs(self.cfg)[:12]
            hint(f"  Current: {self.ref}")
            if refs:
                hint("  Try: " + "  ".join(refs[:6]))
            hint("  Usage: /model provider:model   (tab completes)")
            return
        try:
            spec, model = resolve_ref(self.cfg, arg)
        except ProviderError as exc:
            error(exc.message, exc.hint)
            return
        if spec.needs_key and not key_for(spec)[0]:
            error(f"No API key for {spec.name}", f"Add one: kunji keys add {spec.id}")
            return
        self.spec, self.model = spec, model
        success(f"Switched to {self.ref}", "conversation kept")

    def cmd_models(self, arg: str) -> None:
        try:
            with Steps() as steps, make_provider(self.spec) as provider:
                models = steps.run(f"Fetching models from {self.spec.name}",
                                   provider.list_models, done=lambda m: f"{len(m)} models")
        except ProviderError as exc:
            error(exc.message, exc.hint)
            return
        save_models_cache(self.spec.id, models)
        shown = [m for m in models if arg.lower() in m.lower()] if arg else models
        rows = [[m, "current" if m == self.model else ""] for m in shown[:40]]
        selected = next((i for i, r in enumerate(rows) if r[0] == self.model), None)
        self.console.print(ResponsiveTable(
            [Column("Model", min_width=12, ratio=1), Column("", priority=1, min_width=7)],
            rows, selected=selected, title=f"{self.spec.name} models"))
        if len(shown) > 40:
            hint(f"  …and {len(shown) - 40} more. Filter: /models <text>")
        hint("  Switch: /model " + self.spec.id + ":<model>")

    def cmd_system(self, arg: str) -> None:
        if not arg:
            hint(f"  System prompt: {self.system or '(none)'}")
            hint("  Set: /system You are a concise assistant.   Clear: /system off")
            return
        self.system = "" if arg.lower() in {"off", "none", "clear"} else arg
        success("System prompt cleared" if not self.system else "System prompt updated")

    def cmd_cost(self, _: str) -> None:
        status = usage.check_budget(self.cfg, self.spec.id)
        rows = [
            ("This session", fmt_money(self.cfg, self.session_cost) +
             (f"  (+{self.unpriced} unpriced)" if self.unpriced else "")),
            (f"Today · {self.spec.id}", fmt_money(self.cfg, usage.spent_today_usd(self.spec.id))),
            ("Today · all", fmt_money(self.cfg, usage.spent_today_usd())),
        ]
        if status.state != "none":
            rows.append(("Budget", f"{fmt_money(self.cfg, None, display_amount=status.limit)} "
                         f"({status.scope})"))
        price = self.catalog.price_for(self.spec.id, self.model, self.spec.openrouter_prefix)
        rows.append(("Price / 1M tok", "unknown — set one with kunji config" if price is None else
                     f"{fmt_money(self.cfg, price.input)} in · "
                     f"{fmt_money(self.cfg, price.output)} out  ({price.source})"))
        self.console.print(Card(rows, title="Cost"))

    def cmd_retry(self, _: str) -> None:
        if not self.messages:
            hint("  Nothing to retry yet.")
            return
        if self.messages[-1].role == "assistant":
            self.messages.pop()
        if self.messages and self.messages[-1].role == "user":
            self.send(self.messages[-1].content, already_added=True)

    def cmd_clear(self, _: str) -> None:
        self.messages.clear()
        success("Started a fresh conversation")

    def cmd_save(self, arg: str) -> None:
        if not self.messages:
            hint("  Nothing to save yet.")
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        path = Path(arg or f"kunji-chat-{stamp}.md").expanduser()
        lines = [f"# kunji chat · {self.ref} · {time.strftime('%Y-%m-%d %H:%M')}", ""]
        for m in self.messages:
            lines += [f"## {'You' if m.role == 'user' else 'Assistant'}", "", m.content, ""]
        try:
            path.write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            error(f"Could not save: {exc}")
            return
        success(f"Saved to {path}")
