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

### How Prices are Found
Kunji needs to know how much a model costs to track your budgets and display live costs. Because model prices change frequently, Kunji uses a three-tier fallback system to find the price. **The first match wins:**

1. **Your overrides:** You can manually set a price in this config file using the `[pricing."provider:model"]` format (see the example below). This is checked first and overrides everything else.
2. **Kunji's catalog:** If you haven't set an override, Kunji checks its built-in, curated list of prices. This list is maintained by the Kunji team for popular models.
3. **OpenRouter:** If the model isn't in the curated list, Kunji will fetch the public pricing data from OpenRouter's model list. This data is cached locally for 24 hours to avoid constant network requests.

*Note: All prices in the config and catalog are represented in **USD per 1 million tokens**, regardless of the display currency you choose.*

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
