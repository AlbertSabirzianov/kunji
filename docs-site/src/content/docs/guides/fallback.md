---
title: "Fallback models"
description: "Keep chatting when an AI provider is rate-limited or down. kunji automatically retries on the next model you choose."
sidebar:
  order: 11
---

If your model is rate-limited, overloaded or unreachable, kunji can try another model
automatically.

## Set it up

```bash
kunji config set fallback '["groq:llama-3.3-70b-versatile", "ollama:llama3.2"]'
```

kunji tries your model first, then each fallback in order:

```
! OpenAI rate limit or quota reached: …
  Trying fallback groq:llama-3.3-70b-versatile
```

## When it kicks in

| Situation | Falls back? |
| --- | --- |
| Rate limit or quota (HTTP 429) | Yes |
| Provider server error (5xx) or overloaded | Yes |
| Network problem (can't connect) | Yes |
| Wrong or expired key (401/403) | No; fix the key |
| Model not found (404) | No; check the name |
| The answer had already started | No; you see an error instead |

Fallbacks without a saved key are skipped. A local [Ollama](/kunji/docs/guides/local-models-ollama/)
model makes a good last fallback because it works offline.
