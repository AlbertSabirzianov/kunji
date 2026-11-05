<div align="center">

# kunji (कुंजी)

**Every AI model in one terminal, with your own keys. See what every answer costs.**

```bash
pip install kunji
```

[![PyPI](https://img.shields.io/pypi/v/kunji?style=flat-square&labelColor=1f2328&color=3ddc84)](https://pypi.org/project/kunji/)
[![CI](https://img.shields.io/github/actions/workflow/status/testwithsuraj/kunji/ci.yml?branch=main&style=flat-square&label=CI&labelColor=1f2328)](https://github.com/testwithsuraj/kunji/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-3ddc84?style=flat-square&labelColor=1f2328)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3ddc84?style=flat-square&labelColor=1f2328&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Providers](https://img.shields.io/badge/providers-10%2B-3ddc84?style=flat-square&labelColor=1f2328)](#providers)
[![Platforms](https://img.shields.io/badge/windows%20%7C%20macos%20%7C%20linux-3ddc84?style=flat-square&labelColor=1f2328&label=runs%20on)](#install)

<img src="https://raw.githubusercontent.com/testwithsuraj/kunji/main/assets/demo.gif" alt="kunji demo: the menu, a chat with Claude, switching to Groq mid-conversation with /model, and /cost" width="860">

[Website](https://testwithsuraj.github.io/kunji/) · [Documentation](https://testwithsuraj.github.io/kunji/docs/) · [Install](#install) · [Commands](#commands) · *Kunji (कुंजी) means "key" in Hindi.*

</div>

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
- **Saved prompts.** `kunji @commit` writes a commit message from your staged changes;
  `@explain`, `@review`, `@fix`, `@summarize`, `@translate` — or make your own.
- **Chat history.** Every chat is saved on your computer. Continue with `kunji chat -c`,
  search with `kunji history search`.
- **Attach files.** `/file app.py` in chat, or `kunji ask -f app.py "what does this do?"`.
- **Menu or commands.** Run `kunji` for an arrow-key menu that stays open until you exit;
  every action is also a command for scripts.
- **Looks professional.** Minimal monochrome design, responsive to any terminal size.

<table>
<tr>
<td><img src="https://raw.githubusercontent.com/testwithsuraj/kunji/main/assets/compare.gif" alt="kunji compare: one prompt, three models, fastest and cheapest marked"><br><sub><b>Compare</b>: one prompt, several models</sub></td>
</tr>
</table>

<sub>Demos are recordings of the real CLI; answers come from a local mock server
(<code>scripts/demo/</code>), so no keys or money were used.</sub>

## Install

Requires Python 3.11+.

```bash
pip install kunji
```

If `pip` isn't found or shows an error, run it through Python instead:

| System | Command |
| --- | --- |
| Windows | `python -m pip install kunji` (or `py -m pip install kunji`) |
| macOS | `python3 -m pip install kunji` |
| Linux | `python3 -m pip install --user kunji` (if it says "externally managed", use `pipx install kunji`) |

No Python on Windows? Download `kunji-windows-x64.exe` from the
[latest release](https://github.com/testwithsuraj/kunji/releases/latest) and run it from a terminal.
Linux: `kunji-linux-x64`.

Update later with `pip install -U kunji`. If the `kunji` command isn't found after installing,
`python -m kunji` always works.

`winget`, Scoop and Homebrew packages are on the [roadmap](ROADMAP.md).

## Quick start

```bash
kunji                     # opens the menu: add a provider, then start a chat
```

Prefer commands? `kunji keys add`, then `kunji chat`.

Free and local? Install [Ollama](https://ollama.com), then `kunji keys add ollama`.

## Commands

| Command | What it does |
| --- | --- |
| `kunji` | Interactive menu (stays open until you choose Exit) |
| `kunji chat` | Chat (`-m provider:model`, `-s "system prompt"`, `-c` continue last, `--resume <id>`) |
| `kunji ask "…"` | One-shot answer. Reads piped input. `-f file` to attach, `--raw` for scripts |
| `kunji @name "…"` | Run a saved prompt, e.g. `kunji @commit`, `git diff \| kunji @review` |
| `kunji prompts` | List prompts; `add`, `edit`, `show`, `remove` your own |
| `kunji history` | Saved chats; `search`, `show`, `export`, `delete` |
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
| `/file path` | Attach a text file to your next message (tab completes paths) |
| `@name text` | Use a saved prompt, e.g. `@explain this error` |
| `/prompts` · `/history` | List saved prompts · recent chats |
| `/system …` | Set the system prompt |
| `/retry` · `/new` · `/save [file]` | Regenerate · new conversation · export markdown |
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

All options: [docs/CONFIG.md](docs/CONFIG.md). Every command with examples: [docs/COMMANDS.md](docs/COMMANDS.md). Full documentation: **[testwithsuraj.github.io/kunji/docs](https://testwithsuraj.github.io/kunji/docs/)**.

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
