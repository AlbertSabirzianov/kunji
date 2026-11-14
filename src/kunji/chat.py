"""Interactive chat session."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pyperclip
from rich.live import Live
from rich.text import Text

from kunji import attachments, checkin, history, prompts, usage
from kunji.catalog import Catalog, fmt_money, refresh_in_background
from kunji.config import Config, cache_dir, data_dir, ensure_dir
from kunji.engine import TurnResult, fallback_chain, stream_turn
from kunji.providers import Message, ProviderError, ProviderSpec, make_provider, resolve_ref
from kunji.providers.registry import all_specs, key_for
from kunji.ui import (
    Capped,
    Column,
    ResponsiveTable,
    Steps,
    StreamView,
    Strip,
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
    def __init__(
        self,
        cfg: Config,
        model_ref: str | None = None,
        system: str | None = None,
        resume: history.ChatRecord | None = None,
        from_menu: bool = False,
    ):
        self.cfg = cfg
        self.from_menu = from_menu
        self.console = get_console()
        self.spec, self.model = resolve_ref(cfg, model_ref or (resume.model if resume else None))
        if system is None:
            system = resume.system if resume else str(cfg.get("chat.system_prompt") or "")
        self.system = system
        self.record = resume
        self.resumed = resume is not None
        self.messages: list[Message] = [
            Message(m["role"], m["content"])
            for m in (resume.messages if resume else [])
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]
        self.pending: list[attachments.Attachment] = []
        self.save_history = bool(cfg.get("chat.history", True))
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
            ("Provider", self.spec.name, 2),
            ("Model", self.model, 0),
            (
                "Key",
                "local"
                if not self.spec.needs_key
                else ("keychain" if source == "keychain" else source.replace("env:", "")),
                4,
            ),
            ("Today", fmt_money(self.cfg, usage.spent_today_usd()), 3),
            ("State", status_text("READY"), 1),
        ]
        if status.state != "none":
            rows.insert(
                4,
                (
                    "Budget",
                    f"{fmt_money(self.cfg, None, display_amount=status.spent)}"
                    f" / {fmt_money(self.cfg, None, display_amount=status.limit)}",
                    3,
                ),
            )
        self.console.print(Strip(rows, title="kunji chat"))
        if not self.from_menu:
            from kunji.upgrade import notice

            line = notice(self.cfg)
            if line:
                self.console.print(Capped(line))
        if self.resumed and self.record:
            n = self.record.turns
            hint(
                f"  Resumed chat {self.record.id}: {self.record.title}  "
                f"({n} earlier message{'s' if n != 1 else ''})"
            )
            last = next((m for m in reversed(self.messages) if m.role == "assistant"), None)
            if last:
                import re

                plain = re.sub(r"```[\s\S]*?```", " [code] ", last.content)
                plain = re.sub(r"[*_`#>]+", "", plain)
                preview = " ".join(plain.split())
                hint("  Last answer: " + (preview[:140] + "…" if len(preview) > 140 else preview))
        self.console.print(
            Capped(
                keys_line(
                    [
                        ("enter", "send"),
                        ("alt+enter", "newline"),
                        ("/", "commands"),
                        ("ctrl+d", "back to menu" if self.from_menu else "quit"),
                    ]
                )
            )
        )
        self.console.print()

    # Main loop -----------------------------------------------------------------
    def run(self) -> None:
        self.header()
        history = ensure_dir(data_dir()) / "history.txt"
        session = chat_prompt(
            str(history),
            lambda: configured_refs(self.cfg),
            self.toolbar,
            prompt_names=lambda: list(prompts.all_prompts()),
        )
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
            if text.startswith("@") and len(text) > 1 and not text.startswith("@@"):
                self.run_prompt(text)
                continue
            self.send(text.removeprefix("@") if text.startswith("@@") else text)
        self.goodbye()

    def goodbye(self) -> None:
        spent = fmt_money(self.cfg, self.session_cost)
        replies = f"{self.turns} repl{'y' if self.turns == 1 else 'ies'}"
        self.console.print(Text(f"  {replies} · {spent} this session", style="k.dim"))
        if self.record and self.save_history and self.turns:
            hint(
                f"  Saved as chat {self.record.id}. Continue later: kunji chat --resume "
                f"{self.record.id}"
            )
        latest = checkin.cached_update_notice()
        if latest:
            hint(f"  kunji {latest} is available — upgrade: kunji upgrade")

    # Sending -------------------------------------------------------------------
    def budget_allows(self, spec: ProviderSpec) -> bool:
        status = usage.check_budget(self.cfg, spec.id)
        limit = fmt_money(self.cfg, None, display_amount=status.limit)
        spent = fmt_money(self.cfg, None, display_amount=status.spent)
        scope = "all providers" if status.scope == "all" else spec.name
        if status.state == "block":
            error(
                f"Daily budget reached for {scope}: {spent} / {limit}",
                f"Raise it with: kunji budget set {status.scope} <amount>",
            )
            return False
        if status.state == "warn" and status.scope not in self.warned_budget:
            self.warned_budget.add(status.scope)
            warn(f"80% of today's budget used for {scope}: {spent} / {limit}")
        return True

    def run_prompt(self, line: str) -> None:
        name, _, rest = line[1:].partition(" ")
        try:
            prompt = prompts.get(name)
            content = prompts.render(prompt, rest)
        except prompts.PromptError as exc:
            error(str(exc), exc.hint)
            return
        hint(f"  Using @{prompt.name}: {prompt.description}")
        self.send(content, title=line)

    def send(self, text: str, already_added: bool = False, title: str | None = None) -> None:
        if not self.budget_allows(self.spec):
            return
        attached = list(self.pending)
        if not already_added:
            self.messages.append(Message("user", attachments.with_files(text, attached)))
        result = self._answer_with_fallback()
        if result is None:
            self.messages.pop()
            hint("  Your message was not sent. Press ↑ to edit and try again.")
            return
        if attached:
            self.pending.clear()
        if self.record is None and self.save_history:
            self.record = history.new_record(self.ref, self.system)
            names = ", ".join(a.path.name for a in attached)
            self.record.title = history.make_title(
                title or (text if text.strip() else f"Files: {names}")
            )
        if result.text:
            self.messages.append(Message("assistant", result.text))
            self.console.print(Capped(answer(result.text)))
            self.save()
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
                        self.cfg,
                        spec,
                        model,
                        self.messages,
                        self.system,
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

    def save(self) -> None:
        if not self.save_history or not self.messages:
            return
        if self.record is None:
            self.record = history.new_record(self.ref, self.system)
        self.record.model = self.ref
        self.record.system = self.system
        self.record.messages = [asdict(m) for m in self.messages]
        try:
            history.save(self.record)
        except OSError as exc:
            warn(f"Could not save this chat: {exc}")

    # Slash commands ------------------------------------------------------------
    COMMAND_HANDLERS: dict[str, str] = {
        "/help": "cmd_help",
        "/model": "cmd_model",
        "/models": "cmd_models",
        "/system": "cmd_system",
        "/cost": "cmd_cost",
        "/retry": "cmd_retry",
        "/copy": "cmd_copy",
        "/clear": "cmd_clear",
        "/save": "cmd_save",
        "/new": "cmd_clear",
        "/file": "cmd_file",
        "/history": "cmd_history",
        "/prompts": "cmd_prompts",
    }
    EXIT_COMMANDS: tuple[str, ...] = ("/exit", "/quit", "/q")

    @classmethod
    def registered_commands(cls) -> list[str]:
        return list(cls.COMMAND_HANDLERS) + list(cls.EXIT_COMMANDS)

    def command(self, line: str) -> str | None:
        name, _, arg = line.partition(" ")
        arg = arg.strip()
        if name in self.EXIT_COMMANDS:
            return "exit"
        handler_name = self.COMMAND_HANDLERS.get(name)
        if handler_name is None:
            error(f"Unknown command {name}", "Type /help to see all commands")
            return None
        getattr(self, handler_name)(arg)
        return None

    def cmd_help(self, _: str) -> None:
        rows = [[cmd, desc] for cmd, desc in SLASH_COMMANDS.items()]
        cols = [Column("Command", min_width=8), Column("What it does", min_width=12, ratio=1)]
        self.console.print(ResponsiveTable(cols, rows, title="Commands"))
        self.console.print(
            Capped(
                keys_line(
                    [
                        ("enter", "send"),
                        ("alt+enter / ctrl+j", "newline"),
                        ("↑", "history"),
                        ("ctrl+c", "stop reply"),
                        ("ctrl+d", "quit"),
                    ]
                )
            )
        )
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
                models = steps.run(
                    f"Fetching models from {self.spec.name}",
                    provider.list_models,
                    done=lambda m: f"{len(m)} models",
                )
        except ProviderError as exc:
            error(exc.message, exc.hint)
            return
        save_models_cache(self.spec.id, models)
        shown = [m for m in models if arg.lower() in m.lower()] if arg else models
        rows = [[m, "current" if m == self.model else ""] for m in shown[:40]]
        selected = next((i for i, r in enumerate(rows) if r[0] == self.model), None)
        self.console.print(
            ResponsiveTable(
                [Column("Model", min_width=12, ratio=1), Column("", priority=1, min_width=7)],
                rows,
                selected=selected,
                title=f"{self.spec.name} models",
            )
        )
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
            (
                "Session",
                fmt_money(self.cfg, self.session_cost)
                + (f" +{self.unpriced}?" if self.unpriced else ""),
                0,
            ),
            (f"Today {self.spec.id}", fmt_money(self.cfg, usage.spent_today_usd(self.spec.id)), 2),
            ("Today all", fmt_money(self.cfg, usage.spent_today_usd()), 1),
        ]
        if status.state != "none":
            rows.append(
                (
                    "Budget",
                    fmt_money(self.cfg, None, display_amount=status.limit) + f" ({status.scope})",
                    3,
                )
            )
        price = self.catalog.price_for(self.spec.id, self.model, self.spec.openrouter_prefix)
        rows.append(
            (
                "Price / 1M",
                "unknown"
                if price is None
                else f"{fmt_money(self.cfg, price.input)} in · "
                f"{fmt_money(self.cfg, price.output)} out",
                4,
            )
        )
        self.console.print(Strip(rows, title="Cost"))
        if price is None:
            hint("  No known price for this model. Set one: see docs/CONFIG.md (pricing)")

    def cmd_retry(self, _: str) -> None:
        if not self.messages:
            hint("  Nothing to retry yet.")
            return
        if self.messages[-1].role == "assistant":
            self.messages.pop()
        if self.messages and self.messages[-1].role == "user":
            self.send(self.messages[-1].content, already_added=True)

    def cmd_copy(self, _: str) -> None:
        for message in reversed(self.messages):
            if message.role == "assistant":
                try:
                    pyperclip.copy(message.content)
                except (pyperclip.PyperclipException, OSError):
                    warn("Could not copy to the clipboard.")
                else:
                    success("Copied the latest assistant response")
                return

        hint("  No response to copy yet.")

    def cmd_clear(self, _: str) -> None:
        self.messages.clear()
        self.pending.clear()
        self.record = None
        self.resumed = False
        success("Started a new conversation")

    def cmd_file(self, arg: str) -> None:
        if not arg:
            if not self.pending:
                hint("  Usage: /file path/to/file.py   (tab completes paths; repeat for more)")
                return
            for a in self.pending:
                hint(f"  📎 {a.display}  {a.size / 1000:.1f} KB")
            hint("  These go with your next message. Remove them: /file clear")
            return
        if arg == "clear":
            self.pending.clear()
            success("Attachments removed")
            return
        import shlex

        try:
            paths = shlex.split(arg, posix=False)
        except ValueError:
            paths = [arg]
        try:
            items = [attachments.load(p) for p in paths]
            attachments.check_total(self.pending + items)
        except (attachments.AttachmentError, OSError) as exc:
            error(str(exc))
            return
        self.pending += items
        for a in items:
            success(f"Attached {a.display}", f"{a.size / 1000:.1f} KB, sent with your next message")

    def cmd_history(self, arg: str) -> None:
        records = history.search(arg) if arg else None
        rows_src = [h.record for h in records] if records is not None else history.list_all()
        rows = [
            [
                r.id,
                r.title,
                r.model.split(":", 1)[-1],
                str(r.turns),
                time.strftime("%d %b %H:%M", time.localtime(r.updated)),
            ]
            for r in rows_src[:10]
        ]
        self.console.print(
            ResponsiveTable(
                [
                    Column("ID", min_width=6),
                    Column("Title", min_width=12, ratio=1),
                    Column("Model", priority=2, min_width=8),
                    Column("Msgs", priority=3, min_width=4, justify="right"),
                    Column("Updated", priority=1, min_width=12),
                ],
                rows,
                title="Search results" if arg else "Recent chats",
                compact=True,
                empty="No saved chats yet." if not arg else "Nothing matched.",
            )
        )
        hint("  Continue one: exit, then kunji chat --resume <id>")

    def cmd_prompts(self, _: str) -> None:
        rows = [
            [f"@{p.name}", p.description, "built-in" if p.builtin else "yours"]
            for p in prompts.all_prompts().values()
        ]
        self.console.print(
            ResponsiveTable(
                [
                    Column("Prompt", min_width=8),
                    Column("What it does", min_width=12, ratio=1),
                    Column("", priority=2, min_width=8),
                ],
                rows,
                title="Saved prompts",
                compact=True,
            )
        )
        hint("  Use one: @explain <text>   Create your own: kunji prompts add <name>")

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
