---
title: "Configuration"
description: "Every kunji setting in config.toml, with defaults and examples. Change them with kunji config set or the Settings menu."
sidebar:
  order: 30
---

Settings live in `config.toml` (find it with `kunji config path`). Change them in three ways:

- the menu: **Settings**
- a command: `kunji config set <key> <value>`
- editing `config.toml` in any text editor

API keys are **never** stored in this file.

```bash
kunji config show                          # everything
kunji config get display.currency          # one value
kunji config set display.currency INR      # change one
kunji config unset chat.system_prompt      # back to the default
```

## All settings

| Key | Default | What it does |
| --- | --- | --- |
| `default_model` | — | Model used when you don't pass `-m`, as `provider:model` |
| `fallback` | `[]` | Models to try when yours fails ([guide](/kunji/docs/guides/fallback/)) |
| `chat.system_prompt` | `""` | System prompt for new chats |
| `chat.max_tokens` | `4096` | Longest answer, in tokens |
| `chat.history` | `true` | Save chats on this computer ([guide](/kunji/docs/guides/chat-history/)) |
| `display.currency` | `USD` | Currency for costs: `USD`, `INR`, `EUR`, `GBP`, `JPY` or any code |
| `display.usd_rate` | `1.0` | How many units of your currency per 1 US dollar |
| `display.max_width` | `100` | Widest that kunji draws content, in columns |
| `budget.daily.<provider>` | — | Daily limit for one provider, in your currency |
| `budget.daily.all` | — | Daily limit for all providers together |
| `updates.check` | `true` | Daily check for a new version |
| `network.catalog` | `true` | Daily download of public price lists |
| `cloud.url` | `""` | Optional kunji cloud server (off when empty) |

## Example config.toml

```toml
default_model = "anthropic:claude-sonnet-4-5"
fallback = ["groq:llama-3.3-70b-versatile", "ollama:llama3.2"]

[chat]
system_prompt = ""
max_tokens = 4096
history = true

[display]
currency = "INR"
usd_rate = 84
max_width = 100

[budget.daily]
all = 400
openai = 150

[updates]
check = true

[network]
catalog = true

[providers.openai]                  # written by `kunji keys add`
default_model = "gpt-4o-mini"
# base_url = "https://my-proxy.example.com/v1"

[custom_providers.lmstudio]         # written by `kunji providers add`
name = "LM Studio"
base_url = "http://localhost:1234/v1"
needs_key = false

[pricing."groq:llama-3.3-70b-versatile"]   # your own price, USD per 1M tokens
input = 0.59
output = 0.79
```

## Values from the command line

`kunji config set` understands `true`/`false`, numbers and JSON lists:

```bash
kunji config set chat.history false
kunji config set chat.max_tokens 8192
kunji config set fallback '["groq:llama-3.3-70b-versatile"]'
```
