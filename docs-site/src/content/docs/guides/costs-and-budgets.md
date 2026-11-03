---
title: "Costs and budgets"
description: "Track how much your AI API usage costs in kunji, show costs in rupees or any currency, and set daily budgets per provider."
sidebar:
  order: 7
---

You pay each provider directly. kunji helps you see what you're spending and stop before it
gets out of hand.

## See costs as you go

Every answer ends with a line like:

```
claude-sonnet · 1,204 in · 380 out · $0.0093 · 3.4s
```

- `/cost` in a chat shows this chat's cost, today's cost and the model's price.
- The bar at the bottom of the chat shows today's total.

## Usage reports

```bash
kunji usage          # last 7 days
kunji usage -d 30    # last 30 days
```

A table per provider and model with requests, tokens and cost. Usage is recorded on your
computer only.

## Daily budgets

```bash
kunji budget set openai 2      # OpenAI: max 2 per day
kunji budget set all 5         # all providers together: max 5 per day
kunji budget show
kunji budget clear openai
```

- At **80%** of a budget, kunji warns you once per chat.
- At **100%**, kunji stops sending messages to that provider until tomorrow (or until you
  raise the limit).
- Amounts are in your display currency.

:::caution
kunji's numbers are estimates based on public price lists. Your provider's billing page is
always the real number. Many providers also let you set a hard spending limit in their
dashboard; it's a good idea to set one there too.
:::

## Show costs in your currency

```bash
kunji config set display.currency INR
kunji config set display.usd_rate 84      # how many rupees per 1 US dollar
```

Or **Settings → Currency** in the menu. Prices are tracked in US dollars and converted with
your rate, so update it now and then.

## When a price is unknown

If kunji doesn't know a model's price, the cost shows as `—` and the usage table marks it with
`+?`. You can set the price yourself (US dollars per million tokens) in `config.toml`:

```toml
# Example only: copy the real numbers from the provider's pricing page.
[pricing."groq:llama-3.3-70b-versatile"]
input = 0.59    # US dollars per 1 million input tokens
output = 0.79   # US dollars per 1 million output tokens
```

Take the numbers from the provider's pricing page. See
[How costs are calculated](/kunji/docs/concepts/costs/).
