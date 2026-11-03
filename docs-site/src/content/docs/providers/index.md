---
title: "AI providers"
description: "Every AI provider kunji supports, how to get an API key for each, and which ones are free."
sidebar:
  order: 0
---

kunji works with these providers. You need your own API key for each one you use, except
Ollama, which runs on your computer.

| Provider | Id | Free option | Guide |
| --- | --- | --- | --- |
| OpenAI | `openai` | No | [Set up](/kunji/docs/providers/openai/) |
| Anthropic | `anthropic` | No | [Set up](/kunji/docs/providers/anthropic/) |
| Google Gemini | `gemini` | Free tier | [Set up](/kunji/docs/providers/gemini/) |
| Groq | `groq` | Free tier | [Set up](/kunji/docs/providers/groq/) |
| OpenRouter | `openrouter` | Some free models | [Set up](/kunji/docs/providers/openrouter/) |
| DeepSeek | `deepseek` | No | [Set up](/kunji/docs/providers/deepseek/) |
| Mistral | `mistral` | Free tier | [Set up](/kunji/docs/providers/mistral/) |
| xAI | `xai` | No | [Set up](/kunji/docs/providers/xai/) |
| Together AI | `together` | No | [Set up](/kunji/docs/providers/together/) |
| Ollama (local) | `ollama` | Always free | [Set up](/kunji/docs/providers/ollama/) |

Free tiers change over time; check each provider's site.

## Add a provider

```bash
kunji keys add            # pick from the list
kunji keys add gemini     # or name it directly
```

kunji checks the key with the provider before saving it in your OS keychain. A wrong key is
never saved.

## Anything else

Any server with an OpenAI-compatible API also works; see
[Custom servers](/kunji/docs/guides/custom-servers/).

## See what you have

```bash
kunji providers      # every supported provider and whether you have a key
kunji keys list      # your keys, masked
kunji keys test      # check they still work
```
