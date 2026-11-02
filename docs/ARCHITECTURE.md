# Architecture

```
src/kunji/
├── cli.py              Typer commands (entry point: kunji.cli:main)
├── chat.py             Interactive chat session + slash commands
├── compare.py          Parallel multi-model compare
├── engine.py           One turn: stream → measure → price → record; fallback chain
├── providers/
│   ├── base.py         ProviderSpec, Message, Usage, StreamEvent, ProviderError, SSE helper
│   ├── openai_compat.py  Any OpenAI-compatible API (most providers, Ollama, custom)
│   ├── anthropic.py    Anthropic Messages API
│   └── registry.py     Built-in providers, custom servers, "provider:model" refs
├── keystore.py         OS keychain + env vars; mask() and redact()
├── config.py           TOML config, platform paths, atomic writes
├── catalog.py          Prices (your overrides → kunji catalog → OpenRouter), money format
├── usage.py            Local usage ledger (JSONL) and daily budgets
├── checkin.py          PyPI update check; signed cloud check-in client (Ed25519)
├── constants.py        URLs and the public verification keys
└── ui/
    ├── theme.py        Colours (hex only) and the shared Rich console
    ├── components.py   Card, Frame, ResponsiveTable, Steps, StreamView, Tail…
    └── input.py        prompt_toolkit chat input, questionary pickers
```

## Request flow

```
you type → ChatSession.send()
         → usage.check_budget()            (warn 80% / block 100%)
         → engine.fallback_chain()         [(spec, model), fallbacks…]
         → engine.stream_turn()
              → registry.make_provider()   (key from keystore)
              → Provider.stream()          (SSE → StreamEvent text/usage)
              → StreamView in rich.Live    (spinner → streaming markdown tail)
         → Catalog.cost()                  (price lookup)
         → usage.record()                  (local JSONL)
         → answer + meta line printed
```

## Responsive rendering

Every component implements `__rich_console__` and reads `options.max_width` at render time,
capped by `display.max_width` (default 100). Live views (`Steps`, `StreamView`, compare
lanes) re-render about 12 times per second, so resizing the window re-flows them
immediately. `Card` stacks label/value below 56 columns; `ResponsiveTable` hides
low-priority columns that don't fit. `Tail` keeps only the lines that fit on screen while an
answer streams; the full answer is printed when it finishes.

## Data on disk

| What | Where (see `kunji config path`) |
| --- | --- |
| Settings | `config.toml` (no secrets) |
| Usage ledger | `data/usage.jsonl` |
| Chat input history | `data/history.txt` |
| Random install id | `data/install_id` |
| Price & model caches, update check | `cache/*.json` |
| API keys | OS keychain, service name `kunji` |

Set `KUNJI_HOME` to put everything under one folder (handy for tests).

## Cloud check-in (optional, off by default)

When `cloud.url` is set, the client posts `{install_id, version, os, license_key?}` and gets
back `{payload, sig}`. The payload is trusted only if the Ed25519 signature matches a public
key in `constants.CHECKIN_PUBLIC_KEYS`, the `install_id` matches and `expires_at` is in the
future. The signed reply is cached, so it keeps working offline until it expires, and editing
the cache breaks the signature.
