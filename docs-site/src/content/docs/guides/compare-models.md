---
title: "Compare models"
description: "Send the same prompt to several AI models at once with kunji compare and see which is fastest and cheapest, side by side."
sidebar:
  order: 6
---

`kunji compare` sends one prompt to several models at the same time, shows each answer, and
ends with a summary table.

```bash
kunji compare "Write a regex that matches email addresses" \
  -m openai:gpt-4o-mini -m groq:llama-3.3-70b-versatile -m anthropic:claude-sonnet-4-5
```

```
✓ openai:gpt-4o-mini  2.1s · 96 tok
✓ groq:llama-3.3-70b-versatile  0.6s · 88 tok
✓ anthropic:claude-sonnet-4-5  3.0s · 120 tok

┌─  Compare  ──────────────────────────────────────────────────────────┐
│  Model                            Time   Tokens      Cost            │
│──────────────────────────────────────────────────────────────────────│
│  groq:llama-3.3-70b-versatile     0.6s       88   <$0.0001   fastest │
│  openai:gpt-4o-mini               2.1s       96    $0.0001  cheapest │
│  anthropic:claude-sonnet-4-5      3.0s      120    $0.0019           │
└──────────────────────────────────────────────────────────────────────┘
```

*(Example output; your times and prices will differ.)*

## Without choosing models

```bash
kunji compare "Explain recursion"
```

uses your default model plus the default models of your other providers (up to three).

## From the menu

**Compare models** → type the prompt → tick models with **Space** → Enter.

## Good uses

- Pick the cheapest model that's good enough for a task you do often.
- Check an important answer against a second model.
- See how fast a new provider really is.

Every answer is billed by its provider and counted in `kunji usage` as normal.
