# Configuration

Settings live in `config.toml` (find it with `kunji config path`). Edit the file directly
or use `kunji config set <key> <value>`. API keys are never stored here.

```toml
default_model = "anthropic:claude-sonnet-4-5"   # provider:model
fallback = ["groq:llama-3.3-70b-versatile", "ollama:qwen2.5"]

[chat]
system_prompt = ""        # default system prompt
max_tokens = 4096         # max tokens per answer
history = true            # save chats on this computer (kunji history)

[display]
currency = "USD"          # USD, INR, EUR, GBP, JPY or any code
usd_rate = 1.0            # how many units of your currency per 1 USD
max_width = 100           # cap for content width on wide terminals

[budget.daily]            # in your display currency
all = 5                   # all providers combined
openai = 2

[updates]
check = true              # daily PyPI version check

[network]
catalog = true            # fetch public price lists (24h cache)

[cloud]
url = ""                  # kunji cloud (empty = off)
checkin = true

[providers.openai]        # written by `kunji keys add`
default_model = "gpt-4o-mini"
added = "2026-11-02T17:00:00+00:00"
# base_url = "https://my-proxy.example.com/v1"   # optional override

[custom_providers.lmstudio]   # written by `kunji providers add`
name = "LM Studio"
base_url = "http://localhost:1234/v1"
needs_key = false

[pricing."openai:gpt-4o-mini"]  # your own price override, USD per 1M tokens
input = 0.15
output = 0.60
```

## Examples

```bash
kunji config set display.currency INR
kunji config set display.usd_rate 84
kunji config set chat.max_tokens 8192
kunji config set fallback '["groq:llama-3.3-70b-versatile"]'
kunji config set updates.check false
kunji config unset chat.system_prompt
```

## Custom OpenAI-compatible servers

See [Custom providers](CUSTOM_PROVIDERS.md) for a short guide on adding LM Studio, vLLM, or any OpenAI-compatible server (URL, provider id, model reference, and API key).

## Environment variables

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, … | Provider keys (override the keychain) |
| `KUNJI_<PROVIDER>_API_KEY` | Key for any provider, e.g. `KUNJI_LMSTUDIO_API_KEY` |
| `KUNJI_HOME` | Keep config, data and cache in one folder |
| `NO_COLOR` | Disable colours |
