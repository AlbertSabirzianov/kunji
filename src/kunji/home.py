"""Interactive home menu — what you get when you run `kunji` with no command.

Stays open until you choose Exit. Every action is also available as a command
(`kunji keys add`, `kunji compare …`), which is what scripts should use.
"""

from __future__ import annotations

from collections.abc import Callable

import questionary
import typer
from rich.text import Text

from kunji import history, keystore, prompts
from kunji import usage as ledger
from kunji.attachments import AttachmentError
from kunji.catalog import fmt_money
from kunji.config import Config, ConfigError
from kunji.history import HistoryError
from kunji.keystore import KeyStoreError
from kunji.prompts import PromptError
from kunji.providers import ProviderError
from kunji.providers.registry import all_specs, key_for, parse_ref
from kunji.ui import Strip, chip, error, get_console, hint, status_text, success
from kunji.ui.input import PICKER_STYLE

BACK = "__back__"
EXIT = "__exit__"


def _ask(question):
    """Run a questionary question; Ctrl+C or Esc returns None instead of raising."""
    try:
        return question.unsafe_ask()
    except KeyboardInterrupt:
        return None


def select(message: str, choices: list, default=None):
    return _ask(questionary.select(message, choices=choices, default=default, style=PICKER_STYLE,
                                   qmark="◆", pointer="❯", instruction="(↑/↓ enter · ctrl+c back)",
                                   use_shortcuts=False))


def text(message: str, default: str = "", validate=None, multiline: bool = False):
    return _ask(questionary.text(message, default=default, style=PICKER_STYLE, qmark="◆",
                                 validate=validate, multiline=multiline))


def choice(title: str, value: str, note: str = "") -> questionary.Choice:
    label = f"{title:<26}{note}" if note else title
    return questionary.Choice(label, value=value)


class Home:
    def __init__(self) -> None:
        self.console = get_console()
        self.cfg = self._load()

    @staticmethod
    def _load() -> Config:
        from kunji.cli import load_config

        return load_config()

    # Helpers ---------------------------------------------------------------------
    def run_safely(self, fn: Callable, *args, **kwargs) -> None:
        """Run a CLI action and always come back to the menu."""
        try:
            fn(*args, **kwargs)
        except typer.Exit:
            pass
        except (ProviderError, KeyStoreError, PromptError, HistoryError) as exc:
            error(getattr(exc, "message", None) or str(exc), getattr(exc, "hint", ""))
        except (AttachmentError, ConfigError, OSError) as exc:
            error(str(exc))
        except KeyboardInterrupt:
            hint("  cancelled")
        self.cfg = self._load()
        self.console.print()

    def configured(self) -> list[str]:
        out = []
        for pid, spec in all_specs(self.cfg).items():
            if self.cfg.provider_entry(pid) or (spec.needs_key and key_for(spec)[0]):
                out.append(pid)
        return out

    def header(self) -> None:
        default = str(self.cfg.get("default_model") or "")
        pid, model = parse_ref(default) if default else ("", "")
        self.console.print(Text.assemble(chip("kunji"), ("  your keys · every model · one terminal",
                                                         "k.dim")))
        self.console.print(Strip([
            ("Default model", model or "not set", 0),
            ("Provider", pid or "—", 2),
            ("Providers", str(len(self.configured())), 3),
            ("Today", fmt_money(self.cfg, ledger.spent_today_usd()), 1),
            ("State", status_text("READY" if default else "SETUP"), 4),
        ]))

    # Main loop -------------------------------------------------------------------
    def run(self) -> None:
        self.header()
        if not self.configured():
            hint("  Welcome! Add your first provider to get started. "
                 "Free options: Groq, Gemini, or Ollama (local).")
            self.console.print()
            self.run_safely(self._keys_add)
        while True:
            action = select("What would you like to do?", self.main_choices())
            if action in (None, EXIT):
                self.console.print(Text("  bye", style="k.dim"))
                return
            handler = getattr(self, f"do_{action}")
            handler()

    def main_choices(self) -> list:
        has_model = bool(self.cfg.get("default_model"))
        last = history.latest()
        items = []
        if has_model:
            items.append(choice("Start a new chat", "chat", str(self.cfg.get("default_model"))))
            if last:
                items.append(choice("Continue last chat", "continue", last.title[:40]))
        items += [
            choice("Open a saved chat", "history"),
            choice("Run a saved prompt", "prompt", "@explain, @commit, …"),
            choice("Compare models", "compare"),
            questionary.Separator(" "),
            choice("Change default model", "model"),
            choice("Providers and keys", "providers"),
            choice("Usage and budgets", "usage"),
            choice("Settings", "settings"),
            choice("Check setup (doctor)", "doctor"),
            questionary.Separator(" "),
            choice("Exit", EXIT),
        ]
        if not has_model:
            items.insert(0, choice("Add a provider", "add_provider", "start here"))
        return items

    # Actions ---------------------------------------------------------------------
    def _chat(self, record=None) -> None:
        from kunji.chat import ChatSession

        self.console.print()
        ChatSession(self.cfg, resume=record, from_menu=True).run()

    def do_chat(self) -> None:
        self.run_safely(self._chat)

    def do_continue(self) -> None:
        self.run_safely(self._chat, history.latest())

    def do_history(self) -> None:
        records = history.list_all()
        if not records:
            hint("  No saved chats yet. Start one from the menu.")
            self.console.print()
            return
        import time

        items = [choice(r.title[:44], r.id,
                        f"{r.model.split(':', 1)[-1][:18]:<20}"
                        f"{time.strftime('%d %b %H:%M', time.localtime(r.updated))}")
                 for r in records[:30]]
        items += [questionary.Separator(" "), choice("Search chats…", "__search__"),
                  choice("Back", BACK)]
        picked = select("Which chat?", items)
        if picked in (None, BACK):
            return
        if picked == "__search__":
            query = text("Search for")
            if query:
                from kunji.cli import history_search

                self.run_safely(history_search, query.split())
            return
        record = history.find(picked)
        action = select(record.title[:60], [
            choice("Continue this chat", "open"), choice("Show it", "show"),
            choice("Export as markdown", "export"), choice("Delete", "delete"),
            choice("Back", BACK)])
        from kunji import cli

        if action == "open":
            self.run_safely(self._chat, record)
        elif action == "show":
            self.run_safely(cli.history_show, record.id)
        elif action == "export":
            self.run_safely(cli.history_export, record.id, None)
        elif action == "delete" and select("Delete this chat?", [
                choice("No", "no"), choice("Yes, delete it", "yes")]) == "yes":
            self.run_safely(cli.history_delete, record.id, False, True)

    def do_prompt(self) -> None:
        items = [choice(f"@{p.name}", p.name, p.description)
                 for p in prompts.all_prompts().values()]
        items += [questionary.Separator(" "), choice("Create a new prompt…", "__new__"),
                  choice("Back", BACK)]
        picked = select("Which prompt?", items)
        if picked in (None, BACK):
            return
        from kunji import cli

        if picked == "__new__":
            name = text("Name (lowercase, e.g. standup)",
                        validate=lambda v: bool(prompts.NAME_RE.match(v.strip().lower()))
                        or "Use lowercase letters, numbers and dashes")
            if not name:
                return
            body = text("Instructions — use {input} where your text goes "
                        "(alt+enter or esc then enter to finish)", multiline=True)
            if body:
                desc = text("One-line description", default="My prompt") or ""
                self.run_safely(cli.prompts_add, name.strip().lower(), body, desc)
            return
        prompt = prompts.get(picked)
        user_text = ""
        if not prompt.needs_git:
            user_text = text(f"Text for @{prompt.name} (alt+enter or esc then enter to finish)",
                             multiline=True)
            if user_text is None:
                return
        path = _ask(questionary.path("Attach a file? (leave empty to skip)", style=PICKER_STYLE,
                                     qmark="◆"))
        if path is None:
            return
        files = [path.strip()] if path.strip() else None
        self.run_safely(cli.run_prompt, prompt.name, [user_text] if user_text else None,
                        None, files, False)

    def do_compare(self) -> None:
        from kunji.chat import configured_refs
        from kunji.compare import default_refs

        question = text("Prompt to send to every model")
        if not question:
            return
        defaults = set(default_refs(self.cfg))
        refs = configured_refs(self.cfg)[:40]
        if len(refs) < 2:
            hint("  Add another provider (or fetch models) to compare more than one model.")
        picked = _ask(questionary.checkbox(
            "Models to compare (space to tick, enter to start)",
            choices=[questionary.Choice(r, value=r, checked=r in defaults) for r in refs],
            style=PICKER_STYLE, qmark="◆",
            validate=lambda v: bool(v) or "Tick at least one model"))
        if picked:
            from kunji.cli import compare

            self.run_safely(compare, [question], picked)

    def do_model(self) -> None:
        pids = self.configured()
        if not pids:
            hint("  Add a provider first.")
            return self.run_safely(self._keys_add)
        specs = all_specs(self.cfg)
        pid = select("Provider", [choice(specs[p].name, p, self.cfg.provider_entry(p)
                                         .get("default_model", "")) for p in pids]
                     + [choice("Back", BACK)])
        if pid in (None, BACK):
            return
        from kunji.chat import save_models_cache
        from kunji.providers import make_provider
        from kunji.ui import Steps
        from kunji.ui.input import pick_or_type

        found: list[str] = []
        try:
            with Steps() as steps, make_provider(specs[pid]) as provider:
                found = steps.run(f"Fetching models from {specs[pid].name}",
                                  provider.list_models, done=lambda m: f"{len(m)} models")
            save_models_cache(pid, found)
        except ProviderError as exc:
            error(exc.message, exc.hint)
        current = self.cfg.provider_entry(pid).get("default_model", "")
        try:
            model = pick_or_type("Model (type to search)", found, default=current)
        except KeyboardInterrupt:
            model = None
        if model:
            from kunji.cli import use

            self.run_safely(use, f"{pid}:{model.strip()}")

    def _keys_add(self) -> None:
        from kunji.cli import keys_add

        keys_add(None, None, False, False)

    def do_add_provider(self) -> None:
        self.run_safely(self._keys_add)

    def do_providers(self) -> None:
        from kunji import cli

        action = select("Providers and keys", [
            choice("Add or replace a key", "add"), choice("List providers", "list"),
            choice("Test my keys", "test"), choice("Remove a provider", "remove"),
            choice("Add a custom server", "custom", "LM Studio, vLLM, proxy"),
            choice("Back", BACK)])
        if action == "add":
            self.run_safely(self._keys_add)
        elif action == "list":
            self.run_safely(cli.keys_list, True)
        elif action == "test":
            self.run_safely(cli.keys_test, None)
        elif action == "remove":
            pids = self.configured()
            if not pids:
                hint("  Nothing to remove.")
                return
            pid = select("Remove which provider?", [choice(p, p) for p in pids]
                         + [choice("Back", BACK)])
            if pid not in (None, BACK) and select(f"Remove {pid} and its key?", [
                    choice("No", "no"), choice("Yes, remove", "yes")]) == "yes":
                self.run_safely(cli.keys_remove, pid, True)
        elif action == "custom":
            pid = text("Short id (e.g. lmstudio)")
            url = pid and text("Base URL", default="http://localhost:1234/v1")
            if pid and url:
                needs_key = select("Does it need an API key?", [
                    choice("No", "no"), choice("Yes", "yes")]) == "yes"
                self.run_safely(cli.providers_add, pid.strip().lower(), url.strip(), None,
                                not needs_key)

    def do_usage(self) -> None:
        from kunji import cli

        action = select("Usage and budgets", [
            choice("Usage this week", "week"), choice("Usage this month", "month"),
            choice("Show budgets", "budgets"), choice("Set a daily budget", "set"),
            choice("Remove a budget", "clear"), choice("Back", BACK)])
        if action == "week":
            self.run_safely(cli.usage_cmd, 7)
        elif action == "month":
            self.run_safely(cli.usage_cmd, 30)
        elif action == "budgets":
            self.run_safely(cli.budget_show)
        elif action in ("set", "clear"):
            scopes = ["all"] + self.configured()
            scope = select("For which provider?", [
                choice("All providers combined" if s == "all" else s, s) for s in scopes]
                + [choice("Back", BACK)])
            if scope in (None, BACK):
                return
            if action == "clear":
                return self.run_safely(cli.budget_clear, scope)
            currency = str(self.cfg.get("display.currency", "USD"))

            def valid(v: str):
                try:
                    return float(v) > 0 or "Enter an amount above 0"
                except ValueError:
                    return "Enter a number, e.g. 2 or 150"

            amount = text(f"Daily limit in {currency}", validate=valid)
            if amount:
                self.run_safely(cli.budget_set, scope, float(amount))

    def do_settings(self) -> None:
        from kunji import cli

        on = lambda key: "on" if self.cfg.get(key, True) else "off"  # noqa: E731
        action = select("Settings", [
            choice("Currency", "currency", f"{self.cfg.get('display.currency')} "
                                           f"(rate {self.cfg.get('display.usd_rate')})"),
            choice("Save chat history", "history", on("chat.history")),
            choice("Default system prompt", "system",
                   (str(self.cfg.get("chat.system_prompt")) or "none")[:30]),
            choice("Update check", "updates", on("updates.check")),
            choice("Price list download", "catalog", on("network.catalog")),
            choice("Show all settings", "show"), choice("Where files are stored", "path"),
            choice("Back", BACK)])
        if action == "currency":
            cur = select("Currency", [choice(c, c) for c in ("USD", "INR", "EUR", "GBP")]
                         + [choice("Other…", "other")])
            if cur == "other":
                cur = text("Currency code, e.g. AED")
            if not cur:
                return
            rate = "1" if cur == "USD" else text(f"How many {cur} per 1 USD?",
                                                 default=str(self.cfg.get("display.usd_rate")))
            if rate:
                self.run_safely(cli.config_set, "display.currency", cur.upper())
                self.run_safely(cli.config_set, "display.usd_rate", rate)
        elif action in ("history", "updates", "catalog"):
            key = {"history": "chat.history", "updates": "updates.check",
                   "catalog": "network.catalog"}[action]
            value = "false" if self.cfg.get(key, True) else "true"
            self.run_safely(cli.config_set, key, value)
        elif action == "system":
            value = text("System prompt for new chats (empty to clear)",
                         default=str(self.cfg.get("chat.system_prompt") or ""))
            if value is not None:
                self.cfg.set("chat.system_prompt", value)
                self.cfg.save()
                success("System prompt updated" if value else "System prompt cleared")
        elif action == "show":
            self.run_safely(cli.config_show)
        elif action == "path":
            self.run_safely(cli.config_path_cmd)

    def do_doctor(self) -> None:
        from kunji.cli import doctor

        self.run_safely(doctor)


def run_home() -> None:
    if not keystore.backend_available():
        hint("  Note: no OS keychain found; keys must come from environment variables.")
    Home().run()


__all__ = ["Home", "run_home"]
