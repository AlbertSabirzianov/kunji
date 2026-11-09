# Custom OpenAI-compatible servers

Kunji can talk to any server that implements the OpenAI chat completions API
(LM Studio, vLLM, LiteLLM, local proxies, self-hosted models, etc.).

## Add a server

```bash
kunji providers add my-server \
  --base-url https://my-server.example.com/v1 \
  --name "My Server"
```

- `my-server` is the **provider identifier**. Use lowercase letters, numbers and dashes.
- `--base-url` is the **server URL**. It must end with `/v1` for most OpenAI-compatible servers.
- `--name` is optional display name.

For servers that do not require an API key (common for pure local setups):

```bash
kunji providers add local-llm \
  --base-url http://localhost:8000/v1 \
  --no-key
```

## Set the API key

If the server needs a key:

```bash
kunji keys add my-server
```

Or set the environment variable (takes precedence):

```bash
export KUNJI_MY_SERVER_API_KEY=sk-placeholder-key
```

The key is stored only in your OS keychain (or read from the environment). It is never written to `config.toml`.

## Use a model

Models are referenced as `provider:model`:

```bash
kunji chat -m my-server:llama-3-8b
kunji use my-server:llama-3-8b          # set as default
kunji models my-server                  # list available models (if the server supports /models)
```

You can also set a default model for the provider in `config.toml`:

```toml
[providers.my-server]
default_model = "llama-3-8b"
```

## Configuration example

After adding a server the config looks like:

```toml
[custom_providers.my-server]
name = "My Server"
base_url = "https://my-server.example.com/v1"
needs_key = true
```

See also [Configuration](CONFIG.md).

## Notes

- Prefer `https://` for remote servers. Plain `http://` is accepted for local addresses only and will warn.
- Custom providers appear in `kunji providers` and work with chat, ask, compare, budgets and the cost meter exactly like built-in providers.
- Remove one with `kunji providers remove my-server`.
