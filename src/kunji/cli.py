"""kunji command-line interface."""

from __future__ import annotations

import os
import platform
import sys
import time
from datetime import datetime, timezone

import typer
from rich.syntax import Syntax
from rich.text import Text

from kunji import __version__, checkin, keystore
from kunji import usage as ledger
from kunji.catalog import Catalog, fmt_money, refresh
from kunji.config import DEFAULTS, Config, ConfigError, coerce, config_path, data_dir
from kunji.keystore import KeyStoreError, mask
from kunji.providers import Message, ProviderError, make_provider, resolve_ref
from kunji.providers.registry import all_specs, get_spec, key_for, valid_provider_id
from kunji.ui import (
    Capped,
    Card,
    Column,
    Frame,
    ResponsiveTable,
    Steps,
    StreamView,
    answer,
    chip,
    error,
    get_console,
    hint,
    set_max_width,
    status_text,
    success,
    warn,
)

app = typer.Typer(
    name="kunji",
    help="Bring your own key. Every AI model in one clean terminal.",
    add_completion=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,  # never print local variables (could contain keys)
    context_settings={"help_option_names": ["-h", "--help"]},
)
keys_app = typer.Typer(help="Add, list, test and remove provider API keys.", no_args_is_help=True)
budget_app = typer.Typer(help="Daily spending limits.", no_args_is_help=True)
config_app = typer.Typer(help="View and change settings.", no_args_is_help=True)
providers_app = typer.Typer(help="Supported providers and custom servers.",
                            invoke_without_command=True)
app.add_typer(keys_app, name="keys")
app.add_typer(budget_app, name="budget")
app.add_typer(config_app, name="config")
app.add_typer(providers_app, name="providers")

console = get_console()


def load_config() -> Config:
    cfg = Config.load()
    set_max_width(cfg.max_width)
    return cfg


def require_interactive(what: str, alternative: str) -> None:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        error(f"{what} needs an interactive terminal.", alternative)
        raise typer.Exit(2)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # noqa: UP017


def ago(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        then = datetime.fromisoformat(iso)
    except ValueError:
        return "—"
    seconds = (datetime.now(timezone.utc) - then).total_seconds()  # noqa: UP017
    for unit, size in (("week", 604800), ("day", 86400), ("h", 3600), ("min", 60)):
        if seconds >= size:
            n = int(seconds // size)
            return f"{n} {unit}{'s' if n > 1 and unit in ('week', 'day') else ''} ago"
    return "just now"


# Root ---------------------------------------------------------------------------


def version_callback(value: bool) -> None:
    if value:
        console.print(f"kunji {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    model: str = typer.Option(None, "--model", "-m", help="provider:model to chat with."),
    version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True,
        help="Show the version and exit."),
) -> None:
    """Run [bold]kunji[/] with no command to start chatting."""
    if ctx.invoked_subcommand is None:
        chat(model=model, system=None)


def welcome(cfg: Config) -> None:
    console.print(Capped(Text.assemble(chip("kunji"), ("  bring your own key · every model, "
                                                         "one terminal", "k.dim"))))
    console.print()
    console.print(Card([
        ("1", Text.assemble("Add a provider   ", ("kunji keys add", "k.accent"))),
        ("2", Text.assemble("Start chatting   ", ("kunji chat", "k.accent"))),
        ("3", Text.assemble("Compare models   ", ("kunji compare \"your prompt\"", "k.accent"))),
    ], title="Get started", footer=Text("Your keys stay in your OS keychain. "
                                        "You are billed directly by each provider.",
                                        style="k.dim")))


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="provider:model, e.g. openai:gpt-4o"),
    system: str = typer.Option(None, "--system", "-s", help="System prompt for this session."),
) -> None:
    """Interactive chat with streaming answers, /commands and a live cost meter."""
    from kunji.chat import ChatSession

    cfg = load_config()
    if not model and not cfg.get("default_model"):
        welcome(cfg)
        raise typer.Exit()
    require_interactive("Chat", 'For scripts use: kunji ask "your question"')
    ChatSession(cfg, model, system).run()


@app.command()
def ask(
    prompt: list[str] = typer.Argument(None, help="Your question. Piped input is added below it."),
    model: str = typer.Option(None, "--model", "-m", help="provider:model"),
    system: str = typer.Option(None, "--system", "-s", help="System prompt."),
    raw: bool = typer.Option(False, "--raw", help="Plain text output (default when piped)."),
) -> None:
    """One question, one answer. Works with pipes: [dim]npm test 2>&1 | kunji ask "fix this"[/]"""
    from kunji.engine import stream_turn

    cfg = load_config()
    question = " ".join(prompt or []).strip()
    piped = ""
    if not sys.stdin.isatty():
        piped = sys.stdin.read()
        if len(piped) > 200_000:
            warn("Input is large; only the last 200k characters were sent.")
            piped = piped[-200_000:]
    if not question and not piped.strip():
        error("Nothing to ask.", 'Usage: kunji ask "your question"')
        raise typer.Exit(2)
    content = question
    if piped.strip():
        content = f"{question}\n\n```\n{piped.rstrip()}\n```" if question else piped
    spec, model_id = resolve_ref(cfg, model)
    sys_prompt = system if system is not None else str(cfg.get("chat.system_prompt") or "")
    messages = [Message("user", content)]
    plain = raw or not sys.stdout.isatty()
    if plain:
        result = stream_turn(cfg, spec, model_id, messages, sys_prompt,
                             on_text=lambda t: (sys.stdout.write(t), sys.stdout.flush()))
        sys.stdout.write("\n")
        return
    from rich.live import Live

    from kunji.chat import meta_line

    view = StreamView()
    with Live(view, console=console, refresh_per_second=12, transient=True):
        result = stream_turn(cfg, spec, model_id, messages, sys_prompt,
                             on_text=lambda t: setattr(view, "text", view.text + t))
    console.print(Capped(answer(result.text)))
    console.print(meta_line(result, cfg))


@app.command()
def compare(
    prompt: list[str] = typer.Argument(..., help="Prompt to send to every model."),
    model: list[str] = typer.Option(None, "--model", "-m",
                                    help="Repeat for each model. Default: your configured ones."),
) -> None:
    """Same prompt, several models, side by side — with speed and cost."""
    from kunji.compare import default_refs, run_compare

    cfg = load_config()
    refs = list(model or []) or default_refs(cfg)
    if len(refs) < 1:
        error("No models to compare.", "Add providers with: kunji keys add   or pass -m a -m b")
        raise typer.Exit(2)
    if len(refs) == 1:
        hint("  Tip: add more models with -m provider:model")
    run_compare(cfg, " ".join(prompt), refs)


@app.command()
def use(ref: str = typer.Argument(..., help="provider:model to use by default")) -> None:
    """Set your default model."""
    cfg = load_config()
    spec, model = resolve_ref(cfg, ref)
    if spec.needs_key and not key_for(spec)[0]:
        warn(f"No API key for {spec.name} yet.", f"Add one: kunji keys add {spec.id}")
    cfg.set("default_model", f"{spec.id}:{model}")
    entry = cfg.provider_entry(spec.id) or {"added": now_iso()}
    entry["default_model"] = model
    cfg.set(f"providers.{spec.id}", entry)
    cfg.save()
    success(f"Default model is now {spec.id}:{model}")


@app.command()
def models(
    provider: str = typer.Argument(None, help="Provider id (default: your current provider)."),
    search: str = typer.Option("", "--search", "-q", help="Filter by text."),
    limit: int = typer.Option(50, "--limit", "-n", help="Max rows to show."),
) -> None:
    """List models a provider offers (fetched live with your key)."""
    from kunji.chat import save_models_cache
    from kunji.providers.registry import parse_ref

    cfg = load_config()
    pid = provider or parse_ref(str(cfg.get("default_model") or ""))[0]
    if not pid:
        error("Which provider?", "Usage: kunji models openai")
        raise typer.Exit(2)
    spec = get_spec(cfg, pid)
    with Steps() as steps:
        provider_obj = make_provider(spec)
        try:
            found = steps.run(f"Fetching models from {spec.name}", provider_obj.list_models,
                              done=lambda m: f"{len(m)} models")
        finally:
            provider_obj.close()
    save_models_cache(spec.id, found)
    refresh(cfg)
    catalog = Catalog(cfg)
    shown = [m for m in found if search.lower() in m.lower()]
    current = cfg.provider_entry(spec.id).get("default_model")
    rows = []
    for m in shown[:limit]:
        price = catalog.price_for(spec.id, m, spec.openrouter_prefix)
        rows.append([
            m,
            "—" if price is None else fmt_money(cfg, price.input),
            "—" if price is None else fmt_money(cfg, price.output),
            "default" if m == current else "",
        ])
    selected = next((i for i, r in enumerate(rows) if r[3]), None)
    console.print(ResponsiveTable([
        Column("Model", min_width=14, ratio=1),
        Column("In / 1M", priority=2, min_width=8, justify="right"),
        Column("Out / 1M", priority=2, min_width=8, justify="right"),
        Column("", priority=1, min_width=7),
    ], rows, selected=selected, title=f"{spec.name} models", empty="No models matched."))
    if len(shown) > limit:
        hint(f"  …{len(shown) - limit} more. Use --search or --limit.")
    hint(f"  Set default: kunji use {spec.id}:<model>")


# Keys ---------------------------------------------------------------------------


def _choose_provider(cfg: Config) -> str:
    require_interactive("Choosing a provider", "Pass it directly: kunji keys add openai")
    from kunji.ui.input import pick

    specs = all_specs(cfg)
    choices = []
    import questionary

    for pid, spec in specs.items():
        configured = bool(cfg.provider_entry(pid))
        suffix = "  ✓ added" if configured else ""
        choices.append(questionary.Choice(f"{spec.name:<18} {pid}{suffix}", value=pid))
    choice = pick("Which provider?", choices)
    if not choice:
        raise typer.Exit(1)
    return choice


@keys_app.command("add")
def keys_add(
    provider: str = typer.Argument(None, help="Provider id, e.g. openai, anthropic, gemini."),
    model: str = typer.Option(None, "--model", "-m", help="Default model for this provider."),
    key_stdin: bool = typer.Option(False, "--key-stdin",
                                   help="Read the key from stdin (for scripts)."),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip the online key check."),
) -> None:
    """Add or replace a provider's API key (stored in your OS keychain)."""
    from kunji.chat import save_models_cache
    from kunji.ui.input import pick_or_type, secret

    cfg = load_config()
    pid = provider or _choose_provider(cfg)
    spec = get_spec(cfg, pid)

    key: str | None = None
    if spec.needs_key:
        if key_stdin:
            key = sys.stdin.readline().strip()
        else:
            require_interactive("Entering a key",
                                f"Use: echo $KEY | kunji keys add {pid} --key-stdin")
            if spec.key_url:
                hint(f"  Get a key: {spec.key_url}")
            key = secret(f"{spec.name} API key")
        if not key:
            error("No key entered.")
            raise typer.Exit(1)

    found: list[str] = []
    with Steps() as steps:
        if not no_verify:
            provider_obj = make_provider(spec, api_key=key)
            try:
                found = steps.run(f"Verifying with {spec.name}", provider_obj.list_models,
                                  done=lambda m: f"{len(m)} models available")
            except ProviderError as exc:
                if exc.status in (401, 403):
                    steps.current = None
                    raise
                steps.warn("Could not verify right now", "saving anyway")
            finally:
                provider_obj.close()
        if spec.needs_key and key:
            steps.run(f"Saving key to {keystore.backend_name()}", keystore.set_key, spec.id, key)
    if found:
        save_models_cache(spec.id, found)

    current = cfg.provider_entry(spec.id).get("default_model", "")
    chosen = model
    if not chosen:
        if sys.stdin.isatty() and sys.stdout.isatty():
            chosen = pick_or_type("Default model (type to search)", found, default=current)
        else:
            chosen = current or (found[0] if found else "")
    chosen = (chosen or "").strip()

    entry = cfg.provider_entry(spec.id) or {}
    entry.setdefault("added", now_iso())
    if chosen:
        entry["default_model"] = chosen
    cfg.set(f"providers.{spec.id}", entry)
    if chosen and not cfg.get("default_model"):
        cfg.set("default_model", f"{spec.id}:{chosen}")
    cfg.save()

    console.print()
    console.print(Card([
        ("Provider", spec.name),
        ("API key", mask(key) if spec.needs_key else "not needed"),
        ("Stored in", keystore.backend_name() if spec.needs_key else "—"),
        ("Default model", chosen or "—"),
        ("State", status_text("ACTIVE" if found else "UNVERIFIED")),
    ], title="Provider added"))
    hint("  Start chatting: kunji chat" + ("" if cfg.get("default_model", "").startswith(spec.id)
                                         else f" -m {spec.id}:{chosen}"))


@keys_app.command("list")
def keys_list(show_all: bool = typer.Option(False, "--all", "-a", help="Include providers "
                                                                       "without keys.")) -> None:
    """Show which providers have keys (keys are masked)."""
    cfg = load_config()
    rows = []
    default_pid = str(cfg.get("default_model") or "").split(":", 1)[0]
    selected = None
    for pid, spec in all_specs(cfg).items():
        entry = cfg.provider_entry(pid)
        key, source = key_for(spec)
        if not (show_all or entry or key):
            continue
        if not spec.needs_key:
            state, where = "LOCAL", "—"
        elif key:
            state = "ENV" if source.startswith("env:") else "KEY SET"
            where = source.replace("env:", "") if source.startswith("env:") else "keychain"
        else:
            state, where = "MISSING", "—"
        if pid == default_pid:
            selected = len(rows)
        rows.append([pid, mask(key) if spec.needs_key else "—", where,
                     entry.get("default_model", "—"), ago(entry.get("added")),
                     status_text(state)])
    console.print(ResponsiveTable([
        Column("Provider", min_width=9),
        Column("Key", priority=3, min_width=12),
        Column("Source", priority=4, min_width=8),
        Column("Default model", priority=1, min_width=12, ratio=1),
        Column("Added", priority=5, min_width=9),
        Column("Status", priority=0, min_width=7),
    ], rows, selected=selected, empty="No providers yet. Add one: kunji keys add"))
    if selected is not None:
        hint("  Highlighted = your default provider")


@keys_app.command("remove")
def keys_remove(
    provider: str = typer.Argument(..., help="Provider id"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Don't ask for confirmation."),
) -> None:
    """Delete a provider's key from the keychain and forget its settings."""
    cfg = load_config()
    spec = get_spec(cfg, provider)
    if not yes:
        require_interactive("Confirmation", f"Use: kunji keys remove {provider} --yes")
        from kunji.ui.input import confirm

        if not confirm(f"Remove {spec.name} key and settings?", default=False):
            raise typer.Exit(1)
    removed = keystore.delete_key(spec.id)
    cfg.unset(f"providers.{spec.id}")
    if str(cfg.get("default_model") or "").startswith(f"{spec.id}:"):
        cfg.set("default_model", "")
    cfg.save()
    success(f"Removed {spec.name}", "key deleted from keychain" if removed else "no stored key")
    _, source = key_for(spec)
    if source.startswith("env:"):
        warn(f"A key is still set in the environment ({source[4:]}).")


@keys_app.command("test")
def keys_test(provider: str = typer.Argument(None, help="Only test this provider.")) -> None:
    """Check every configured key against its provider."""
    cfg = load_config()
    targets = [provider] if provider else [
        pid for pid, spec in all_specs(cfg).items() if cfg.provider_entry(pid) or key_for(spec)[0]
    ]
    if not targets:
        hint("No providers to test. Add one: kunji keys add")
        return
    failures = 0
    with Steps() as steps:
        for pid in targets:
            spec = get_spec(cfg, pid)
            try:
                prov = make_provider(spec)
            except ProviderError as exc:
                steps.warn(spec.name, exc.message)
                failures += 1
                continue
            try:
                steps.run(spec.name, prov.list_models, done=lambda m: f"{len(m)} models")
            except ProviderError:
                failures += 1
            finally:
                prov.close()
    if failures:
        raise typer.Exit(1)


# Providers ----------------------------------------------------------------------


@providers_app.callback()
def providers_list(ctx: typer.Context) -> None:
    """List supported providers."""
    if ctx.invoked_subcommand:
        return
    cfg = load_config()
    rows = []
    for pid, spec in all_specs(cfg).items():
        kind = "local" if not spec.needs_key else (
            "Anthropic API" if spec.kind == "anthropic" else "OpenAI-compatible")
        if spec.custom:
            kind = "custom"
        key, _ = key_for(spec)
        state = "LOCAL" if not spec.needs_key else ("KEY SET" if key else "—")
        rows.append([pid, spec.name, kind, spec.env_vars[0] if spec.env_vars else "—",
                     status_text(state)])
    console.print(ResponsiveTable([
        Column("ID", min_width=8),
        Column("Name", priority=1, min_width=10),
        Column("Type", priority=3, min_width=10),
        Column("Env variable", priority=4, min_width=12),
        Column("Status", min_width=7),
    ], rows, title="Providers"))
    hint("  Add a custom OpenAI-compatible server: kunji providers add <id> --base-url <url>")


@providers_app.command("add")
def providers_add(
    provider_id: str = typer.Argument(..., help="Short id, e.g. lmstudio"),
    base_url: str = typer.Option(..., "--base-url", help="e.g. http://localhost:1234/v1"),
    name: str = typer.Option(None, "--name", help="Display name"),
    no_key: bool = typer.Option(False, "--no-key", help="Server does not need an API key."),
) -> None:
    """Add a custom OpenAI-compatible server (LM Studio, vLLM, a proxy…)."""
    cfg = load_config()
    if not valid_provider_id(provider_id) or provider_id in all_specs(Config({}, cfg.path)):
        error("Choose a new id using lowercase letters, numbers and dashes.")
        raise typer.Exit(2)
    if not base_url.startswith(("https://", "http://")):
        error("The base URL must start with https:// (or http:// for local servers).")
        raise typer.Exit(2)
    if base_url.startswith("http://") and not any(
        h in base_url for h in ("localhost", "127.0.0.1", "0.0.0.0", "192.168.", "10.")  # noqa: S104
    ):
        warn("This server uses plain http — your key would be sent unencrypted.")
    cfg.set(f"custom_providers.{provider_id}",
            {"name": name or provider_id, "base_url": base_url, "needs_key": not no_key})
    cfg.save()
    success(f"Added {name or provider_id}",
            "next: kunji keys add " + provider_id)


@providers_app.command("remove")
def providers_remove(provider_id: str = typer.Argument(...)) -> None:
    """Remove a custom server."""
    cfg = load_config()
    if not cfg.unset(f"custom_providers.{provider_id}"):
        error(f"No custom provider named {provider_id}.")
        raise typer.Exit(1)
    cfg.unset(f"providers.{provider_id}")
    keystore.delete_key(provider_id)
    cfg.save()
    success(f"Removed {provider_id}")


# Usage & budget -----------------------------------------------------------------


@app.command("usage")
def usage_cmd(
    days: int = typer.Option(7, "--days", "-d", help="How many days to include."),
) -> None:
    """Tokens and cost per model (tracked locally, never uploaded)."""
    cfg = load_config()
    rows_data = ledger.summary(days)
    rows = [[r.provider, r.model, f"{r.requests:,}", f"{r.input_tokens:,}",
             f"{r.output_tokens:,}",
             fmt_money(cfg, r.cost_usd) + (" +?" if r.unknown_cost else "")] for r in rows_data]
    console.print(ResponsiveTable([
        Column("Provider", priority=1, min_width=8),
        Column("Model", min_width=12, ratio=1),
        Column("Requests", priority=3, min_width=8, justify="right"),
        Column("In tok", priority=4, min_width=8, justify="right"),
        Column("Out tok", priority=4, min_width=8, justify="right"),
        Column("Cost", min_width=8, justify="right"),
    ], rows, title=f"Usage · last {days} day{'s' if days != 1 else ''}",
        empty="No usage yet."))
    total = sum(r.cost_usd for r in rows_data)
    console.print(Card([
        ("Total", fmt_money(cfg, total)),
        ("Today", fmt_money(cfg, ledger.spent_today_usd())),
        ("Requests", f"{sum(r.requests for r in rows_data):,}"),
    ]))
    if any(r.unknown_cost for r in rows_data):
        hint("  +? = some requests had no known price. Set one: "
             "kunji config set pricing.\"provider:model\" ... (see docs/CONFIG.md)")


@budget_app.command("set")
def budget_set(
    scope: str = typer.Argument(..., help="Provider id, or 'all' for every provider combined."),
    amount: float = typer.Argument(..., help="Daily limit in your display currency."),
) -> None:
    """Set a daily limit. Kunji warns at 80% and blocks at 100%."""
    cfg = load_config()
    if scope != "all":
        get_spec(cfg, scope)
    if amount <= 0:
        error("The amount must be greater than 0.")
        raise typer.Exit(2)
    cfg.set(f"budget.daily.{scope}", amount)
    cfg.save()
    success(f"Daily budget for {scope}: {fmt_money(cfg, None, display_amount=amount)}")


@budget_app.command("show")
def budget_show() -> None:
    """Show today's spend against each limit."""
    from kunji.catalog import to_display

    cfg = load_config()
    rows = []
    for scope, limit in (cfg.get("budget.daily") or {}).items():
        spent = to_display(cfg, ledger.spent_today_usd(None if scope == "all" else scope))
        limit = float(limit)
        state = "BLOCKED" if spent >= limit else "NEAR LIMIT" if spent >= limit * ledger.WARN_AT \
            else "OK"
        rows.append([scope, fmt_money(cfg, None, display_amount=spent),
                     fmt_money(cfg, None, display_amount=limit), status_text(state)])
    console.print(ResponsiveTable([
        Column("Scope", min_width=8),
        Column("Spent today", priority=1, min_width=10, justify="right"),
        Column("Limit", min_width=8, justify="right"),
        Column("Status", min_width=7),
    ], rows, title="Budgets", empty="No budgets set. Example: kunji budget set openai 2"))


@budget_app.command("clear")
def budget_clear(scope: str = typer.Argument(..., help="Provider id or 'all'.")) -> None:
    """Remove a daily limit."""
    cfg = load_config()
    if cfg.unset(f"budget.daily.{scope}"):
        cfg.save()
        success(f"Removed budget for {scope}")
    else:
        hint(f"No budget set for {scope}.")


# Config -------------------------------------------------------------------------


@config_app.command("path")
def config_path_cmd() -> None:
    """Where kunji keeps its files."""
    from kunji.config import cache_dir

    console.print(Card([
        ("Config", str(config_path())),
        ("Data", str(data_dir())),
        ("Cache", str(cache_dir())),
    ], title="Paths"))


@config_app.command("show")
def config_show() -> None:
    """Print the current settings (contains no API keys)."""
    import tomli_w

    cfg = load_config()
    console.print(Frame(Syntax(tomli_w.dumps(cfg.data), "toml", theme="ansi_dark",
                               background_color="default", word_wrap=True), title="config.toml"))


@config_app.command("get")
def config_get(key: str = typer.Argument(..., help="Dotted key, e.g. display.currency")) -> None:
    """Read one setting."""
    value = load_config().get(key)
    if value is None:
        error(f"{key} is not set.")
        raise typer.Exit(1)
    console.print(str(value))


@config_app.command("set")
def config_set(key: str = typer.Argument(...), value: str = typer.Argument(...)) -> None:
    """Change a setting, e.g. [dim]kunji config set display.currency INR[/]"""
    root = key.split(".", 1)[0]
    if root not in DEFAULTS:
        error(f"Unknown setting '{root}'.", "Known: " + ", ".join(sorted(DEFAULTS)))
        raise typer.Exit(2)
    cfg = load_config()
    cfg.set(key, coerce(value))
    cfg.save()
    success(f"{key} = {cfg.get(key)!r}")


@config_app.command("unset")
def config_unset(key: str = typer.Argument(...)) -> None:
    """Remove a setting (falls back to the default)."""
    cfg = load_config()
    if cfg.unset(key):
        cfg.save()
        success(f"Removed {key}")
    else:
        hint(f"{key} was not set.")


# Doctor & version ---------------------------------------------------------------


@app.command()
def doctor() -> None:
    """Check that everything kunji needs is working."""
    cfg = load_config()
    problems = 0
    with Steps() as steps:
        py = platform.python_version()
        steps.ok(f"Python {py}")
        try:
            cfg.save()
            steps.ok("Config is writable", str(config_path()))
        except OSError as exc:
            steps.warn("Config is not writable", str(exc))
            problems += 1
        if keystore.backend_available():
            def probe() -> None:
                keystore.set_key("kunji-doctor", "probe-value-123456")
                assert keystore.get_key("kunji-doctor")[0] == "probe-value-123456"
                keystore.delete_key("kunji-doctor")
            try:
                steps.run(f"Keychain: {keystore.backend_name()}", probe)
            except Exception:  # noqa: BLE001
                problems += 1
        else:
            steps.warn("No OS keychain found", "use environment variables for keys")
            problems += 1
        configured = [pid for pid, spec in all_specs(cfg).items()
                      if cfg.provider_entry(pid) or key_for(spec)[0]]
        if configured:
            steps.ok("Providers", ", ".join(configured))
        else:
            steps.warn("No providers yet", "run: kunji keys add")
        latest = checkin.check_updates(cfg, force=True) if cfg.get("updates.check", True) else None
        if latest:
            steps.warn(f"Update available: {latest}", "pipx upgrade kunji")
        else:
            steps.ok(f"kunji {__version__}", "up to date or offline")
    if problems:
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version and update status."""
    cfg = load_config()
    latest = checkin.check_updates(cfg)
    console.print(Card([
        ("Version", __version__),
        ("Latest", latest or "you're up to date"),
        ("Python", platform.python_version()),
        ("System", f"{platform.system()} {platform.release()}"),
    ], title="kunji"))


# Entry point --------------------------------------------------------------------


def main() -> None:
    started = time.monotonic()
    try:
        app()
    except ProviderError as exc:
        error(exc.message, exc.hint)
        sys.exit(1)
    except KeyStoreError as exc:
        error(str(exc), exc.hint)
        sys.exit(1)
    except ConfigError as exc:
        error(str(exc), f"Fix or delete the file: {config_path()}")
        sys.exit(1)
    except BrokenPipeError:
        # Output was piped into something that closed early (e.g. `| head`).
        try:
            sys.stdout = open(os.devnull, "w")  # noqa: SIM115
        except OSError:
            pass
        sys.exit(0)
    except KeyboardInterrupt:
        if time.monotonic() - started > 0.2:
            get_console().print(Text("  cancelled", style="k.dim"))
        sys.exit(130)


if __name__ == "__main__":
    main()
