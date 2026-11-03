---
title: "Free local models with Ollama"
description: "Chat with free AI models running on your own computer using Ollama and kunji. No API key, no bill, works offline."
sidebar:
  order: 9
---

[Ollama](https://ollama.com) runs open models on your own computer. With kunji you can chat
with them like any other provider: no key, no bill, and nothing leaves your machine.

## Set up

1. **Install Ollama** from [ollama.com/download](https://ollama.com/download).
2. **Download a model.** Smaller models run on most laptops:

   ```bash
   ollama pull llama3.2
   ```

3. **Add it to kunji:**

   ```bash
   kunji keys add ollama
   ```

   No key is asked for. kunji connects to Ollama at `http://localhost:11434` and lists the
   models you've downloaded. Pick one.

4. **Chat:**

   ```bash
   kunji chat -m ollama:llama3.2
   ```

## Tips

- Model names can contain colons, like `ollama:qwen2.5:7b`. kunji splits only at the first
  colon, so this works.
- Local models cost nothing, so they show `$0` or no price.
- Mix local and cloud in one chat: start with a local model, then `/model openai:gpt-4o-mini`
  for a harder question.
- Use a local model as a fallback when your cloud provider is down; see
  [Fallback models](/kunji/docs/guides/fallback/).

## Ollama on another computer

If Ollama runs on another machine on your network, point kunji at it in `config.toml`:

```toml
[providers.ollama]
base_url = "http://192.168.1.20:11434/v1"
```

## Troubleshooting

**"Could not reach Ollama"**: start Ollama (open the app, or run `ollama serve`) and try
again. Check `ollama list` shows at least one model.
