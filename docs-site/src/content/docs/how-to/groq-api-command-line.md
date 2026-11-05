---
title: "Use the Groq API from the command line"
description: "Call Groq's fast Llama models from your terminal: chat, one-off questions, pipes and scripts, with token counts and cost shown for every answer."
sidebar:
  order: 3
---

[Groq](https://groq.com) runs open models such as Llama very fast and has a free tier. Here's
how to use it from the terminal without writing any code.

## Quick version with curl

Groq's API is OpenAI-compatible, so a raw request looks like this:

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.3-70b-versatile",
       "messages": [{"role": "user", "content": "Explain DNS in one paragraph"}]}'
```

That works, but you get raw JSON back, no conversation memory and no idea what it cost. A
CLI makes it pleasant.

## With kunji

```bash
pip install kunji
kunji keys add groq
```

Get a key at [console.groq.com/keys](https://console.groq.com/keys) and paste it when asked.
It's stored in your OS keychain. Then:

```bash
kunji chat -m groq:llama-3.3-70b-versatile
```

Every answer streams as it's generated and ends with a line like:

```
llama-3.3-70b-versatile · 60 in · 17 out · <$0.0001 · 0.2s
```

Make it your default so you don't need `-m`:

```bash
kunji use groq:llama-3.3-70b-versatile
```

List the models your key can use:

```bash
kunji models groq
```

## In scripts and pipes

```bash
kunji ask -m groq:llama-3.3-70b-versatile "summarize this" -f notes.txt
git log --oneline -20 | kunji ask "write release notes from these commits"
tail -100 server.log | kunji @explain
```

When output is piped, kunji prints plain text, so it's safe to use in scripts. In CI, set
the key as an environment variable instead of using the keychain:

```bash
export GROQ_API_KEY=...
```

## Groq as a fast fallback

If your main provider is rate-limited or down, kunji can retry on Groq automatically:

```bash
kunji config set fallback '["groq:llama-3.3-70b-versatile"]'
```

See [Fallback models](/kunji/docs/guides/fallback/).

## How fast is it, really?

Compare it with your other models on the same prompt:

```bash
kunji compare "explain big-O notation" -m groq:llama-3.3-70b-versatile -m openai:gpt-4o-mini
```

The summary table marks the **fastest** and **cheapest**. See
[Compare models](/kunji/docs/guides/compare-models/).
