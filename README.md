<div align="center">

# kunji

**Bring your own key. Every AI model in one clean, professional terminal.**

*Kunji (कुंजी) means "key" in Hindi.*

[![CI](https://img.shields.io/github/actions/workflow/status/testwithsuraj/kunji/ci.yml?branch=main&style=flat-square&label=CI&labelColor=1f2328)](https://github.com/testwithsuraj/kunji/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-3ddc84?style=flat-square&labelColor=1f2328)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3ddc84?style=flat-square&labelColor=1f2328&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Providers](https://img.shields.io/badge/providers-10%2B-3ddc84?style=flat-square&labelColor=1f2328)](#providers)
[![Platforms](https://img.shields.io/badge/windows%20%7C%20macos%20%7C%20linux-3ddc84?style=flat-square&labelColor=1f2328&label=runs%20on)](#install)

</div>

```
┌─  kunji chat  ─────────────────────────────────────────────────┐
│  Provider     Model            Key         Budget        State │
│────────────────────────────────────────────────────────────────│
│  Anthropic    claude-sonnet    keychain    $0.38 / $2    READY │
└────────────────────────────────────────────────────────────────┘
enter send  ·  alt+enter newline  ·  / commands  ·  ctrl+d quit

› explain recursion in one line
  A function that solves a problem by calling itself on a smaller
  piece of it, until it reaches a case simple enough to answer.
  claude-sonnet · 18 in · 31 out · $0.0005 · 1.2s

› /model groq:llama-3.3-70b-versatile
✓ Switched to groq:llama-3.3-70b-versatile  conversation kept
```

Kunji is a terminal app for chatting with any AI model using **your own API keys**.
You pay each provider directly. Kunji never sees your bill, your keys or your prompts.

## Why kunji

- **One tool, every provider.** OpenAI, Anthropic, Google Gemini, Groq, OpenRouter,
  DeepSeek, Mistral, xAI, Together, Ollama (local), plus any OpenAI-compatible server.
- **Switch models mid-conversation** with `/model` — the conversation carries over.
- **Live cost meter.** Every reply shows tokens and cost. `/cost` and `kunji usage`
  show totals, in your currency.
- **Daily budgets.** Warns at 80%, blocks at 100%, per provider or overall.
- **Compare mode.** One prompt, several models, side by side — fastest and cheapest highlighted.
- **Automatic fallback.** Rate-limited or down? Kunji retries on your next model.
- **Keys in your OS keychain** (Windows Credential Manager, macOS Keychain, Secret Service),
  never in a plain-text file.
- **Pipes.** `npm test 2>&1 | kunji ask "why is this failing?"`
- **Looks professional.** Minimal monochrome design, responsive to any terminal size.

## Install

Requires Python 3.11+.

```bash
pipx install kunji        # recommended
# or
uv tool install kunji
# or
python -m pip install --user kunji
```

Standalone binaries for Windows, macOS and Linux (no Python needed) are attached to each
[GitHub release](https://github.com/testwithsuraj/kunji/releases). `winget`, Scoop and
Homebrew packages are on the [roadmap](ROADMAP.md).

## Quick start

```bash
kunji keys add            # pick a provider, paste your key, choose a default model
kunji                     # start chatting
```

Free and local? Install [Ollama](https://ollama.com), then `kunji keys add ollama`.

## Commands

| Command | What it does |
| --- | --- |
| `kunji` / `kunji chat` | Interactive chat (`-m provider:model`, `-s "system prompt"`) |
| `kunji ask "…"` | One-shot answer. Reads piped input. `--raw` for scripts |
| `kunji compare "…" -m a -m b` | Same prompt to several models, side by side |
| `kunji keys add [provider]` | Add or replace a key (verified, then saved to the keychain) |
| `kunji keys list` / `test` / `remove` | Manage keys (always masked) |
| `kunji models [provider]` | Live model list with prices |
| `kunji use provider:model` | Set your default model |
| `kunji providers` | Supported providers; `providers add` for custom servers |
| `kunji usage` | Tokens and cost per model (stored locally only) |
| `kunji budget set <provider\|all> <amount>` | Daily spending limit |
| `kunji config show` / `set` / `path` | Settings |
| `kunji doctor` | Check Python, config, keychain and providers |

### In chat

| Input | Action |
| --- | --- |
| `/model provider:model` | Switch model (tab completes) |
| `/models [filter]` | List models of the current provider |
| `/cost` | Session and today's cost |
| `/system …` | Set the system prompt |
| `/retry` · `/clear` · `/save [file]` | Regenerate · new conversation · export markdown |
| `enter` · `alt+enter` / `ctrl+j` | Send · new line |
| `ctrl+c` · `ctrl+d` | Stop the reply · quit |

## Providers

| ID | Provider | Key env variable |
| --- | --- | --- |
| `openai` | OpenAI | `OPENAI_API_KEY` |
| `anthropic` | Anthropic | `ANTHROPIC_API_KEY` |
| `gemini` | Google Gemini | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| `groq` | Groq | `GROQ_API_KEY` |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY` |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` |
| `mistral` | Mistral | `MISTRAL_API_KEY` |
| `xai` | xAI | `XAI_API_KEY` |
| `together` | Together AI | `TOGETHER_API_KEY` |
| `ollama` | Ollama (local) | none |

Any OpenAI-compatible server (LM Studio, vLLM, LiteLLM proxy…):

```bash
kunji providers add lmstudio --base-url http://localhost:1234/v1 --no-key
```

## Security and privacy

- API keys are stored **only** in your operating system's credential store, or read from
  environment variables. They are sent **only** to the provider they belong to.
- Kunji's config file never contains keys. Errors are scrubbed so keys never appear on screen.
- Usage and cost history stay on your machine (`kunji config path`).
- Network calls kunji makes on its own: the public model price list (OpenRouter, plus this
  repo's `catalog/pricing.json`) and the PyPI version check. Neither sends anything about you.
  Turn them off with `kunji config set network.catalog false` and
  `kunji config set updates.check false`.
- Found a vulnerability? Please follow [SECURITY.md](SECURITY.md).

Details: [docs/PRIVACY.md](docs/PRIVACY.md).

## Configuration

```bash
kunji config set display.currency INR
kunji config set display.usd_rate 84          # your conversion rate
kunji budget set all 200                      # ₹200/day across every provider
kunji config set fallback '["groq:llama-3.3-70b-versatile", "ollama:qwen2.5"]'
```

All options: [docs/CONFIG.md](docs/CONFIG.md).

## Free and Pro

Everything that runs on your machine is **free and open source, forever** — chat,
switching, keys, cost meter, budgets, compare, fallback, pipes. A future optional
**Pro** plan will add cloud features that need a server (sync across devices, shared team
keys with per-person budgets, a smart router). See [ROADMAP.md](ROADMAP.md).

## Contributing

Bug reports, ideas and pull requests are welcome — start with
[CONTRIBUTING.md](CONTRIBUTING.md). Architecture overview: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

[Apache-2.0](LICENSE). "kunji" and the kunji logo are not covered by the license; please
use a different name for forks.
