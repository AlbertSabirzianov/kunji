---
title: "Switch and pick models"
description: "How to choose a default AI model in kunji, list a provider's models with prices, and switch models in the middle of a conversation."
sidebar:
  order: 2
---

kunji writes models as **`provider:model`**, for example `openai:gpt-4o-mini` or
`groq:llama-3.3-70b-versatile`. The provider part is kunji's id for the company
(see [Providers](/kunji/docs/providers/)); the model part is the provider's own model name.

## See which models a provider has

```bash
kunji models openai
kunji models openrouter --search llama
```

The list comes live from the provider using your key, so it's always current. Where kunji
knows the price, it shows the cost per million input and output tokens.

## Set your default model

From the menu: **Change default model** → pick a provider → type to search → Enter.

Or with a command:

```bash
kunji use anthropic:claude-sonnet-4-5
```

The default is used by `kunji chat`, `kunji ask` and saved prompts unless you pass `-m`.

## Switch in the middle of a chat

```
/model groq:llama-3.3-70b-versatile
✓ Switched to groq:llama-3.3-70b-versatile  conversation kept
```

The whole conversation so far is sent to the new model, so you can ask one model, then ask
another to check or improve the answer. Press **Tab** after `/model ` to complete model names
(models appear after you've listed them once with `/models` or `kunji models`).

## Use a model once

```bash
kunji chat -m mistral:mistral-large-latest
kunji ask -m deepseek:deepseek-chat "Explain big-O notation"
```

## Each provider's default

Every provider you add has its own default model, chosen when you added the key. Writing just
the provider uses it:

```bash
kunji chat -m groq      # uses your default Groq model
```
