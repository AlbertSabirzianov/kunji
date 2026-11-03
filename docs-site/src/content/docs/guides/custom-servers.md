---
title: "Custom servers"
description: "Connect kunji to LM Studio, vLLM, LiteLLM or any OpenAI-compatible API server, local or remote."
sidebar:
  order: 10
---

Any server that speaks the OpenAI chat-completions API works with kunji: LM Studio, vLLM,
LiteLLM, llama.cpp's server, or a company proxy.

## Add a server

```bash
kunji providers add lmstudio --base-url http://localhost:1234/v1 --no-key --name "LM Studio"
kunji keys add lmstudio
kunji chat -m lmstudio:<model>
```

- **id** (`lmstudio`): your short name, lowercase letters, numbers and dashes.
- **`--base-url`**: the address that ends in `/v1` (the part before `/chat/completions`).
- **`--no-key`**: use this if the server doesn't need a key. Otherwise `kunji keys add <id>`
  asks for one and stores it in the keychain.

From the menu: **Providers and keys → Add a custom server**.

## Examples

| Server | Base URL |
| --- | --- |
| LM Studio | `http://localhost:1234/v1` |
| vLLM | `http://localhost:8000/v1` |
| LiteLLM proxy | `http://localhost:4000/v1` |
| llama.cpp server | `http://localhost:8080/v1` |

## Security

Use `https://` for any server that isn't on your own computer or network. kunji warns when
you add a plain `http://` address on the internet, because your key would travel unencrypted.

## Remove a server

```bash
kunji providers remove lmstudio
```

## Point a built-in provider somewhere else

To send a built-in provider through a proxy, set its `base_url`:

```toml
[providers.openai]
base_url = "https://my-proxy.example.com/v1"
```
