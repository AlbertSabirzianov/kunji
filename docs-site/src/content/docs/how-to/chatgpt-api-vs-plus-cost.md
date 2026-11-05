---
title: "ChatGPT API vs ChatGPT Plus: which costs less?"
description: "Compare a ChatGPT Plus subscription with paying per use for the OpenAI API. Worked examples, how to estimate your own cost, and how to track it."
sidebar:
  order: 4
---

ChatGPT Plus is a flat monthly subscription. The OpenAI API charges per use: you pay for
the tokens you send and receive. For many people who mostly ask questions and get help with
code, the API works out much cheaper. For heavy users of the chat app's extra features, Plus
can be better value.

:::note
Prices below are examples at the time of writing. Always check
[openai.com/chatgpt/pricing](https://openai.com/chatgpt/pricing/) and
[openai.com/api/pricing](https://openai.com/api/pricing/) for current numbers.
:::

## How API pricing works

API prices are per **million tokens**, with separate input and output prices. A token is
roughly ¾ of a word, so a 500-word answer is about 650 tokens.

```
cost = input tokens × input price + output tokens × output price
```

Example prices per 1M tokens:

| Model | Input | Output |
| --- | --- | --- |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.00 |

## Worked example

Say you send **50 messages a day**, each with about **500 tokens in** (your question plus some
earlier conversation) and **500 tokens out**. That's 1,500 messages a month.

| Model | Cost per message | Per month |
| --- | --- | --- |
| gpt-4o-mini | 500 × $0.15/1M + 500 × $0.60/1M ≈ $0.0004 | **≈ $0.56** |
| gpt-4o | 500 × $2.50/1M + 500 × $10/1M ≈ $0.0063 | **≈ $9.40** |

ChatGPT Plus costs **$20 a month** in the US (prices vary by country).

Two things push the API cost up:

- **Long conversations.** Every message re-sends the whole chat so far as input. Start a new
  chat when you change topic.
- **Big inputs.** Pasting whole files or logs adds input tokens.

## When Plus is the better deal

- You use features that only exist in the ChatGPT app (image generation, voice, custom GPTs,
  file analysis in the browser).
- You send very long conversations all day with the largest models.
- You want a fixed bill and never think about tokens.

## When the API is the better deal

- You mostly ask questions, write and debug code, or summarize text.
- You want to use **other providers** too (Claude, Gemini, Llama via Groq) without a
  subscription for each.
- You use AI in scripts and the terminal.

## Measure instead of guessing

[kunji](/kunji/docs/introduction/) is a free terminal app that shows the cost of every
answer and keeps a local usage log:

```bash
pip install kunji
kunji keys add openai
kunji chat -m openai:gpt-4o-mini
```

After a week, check your real number:

```bash
kunji usage -d 7
```

Set a daily limit so there are no surprises:

```bash
kunji budget set openai 1
```

Costs can also be shown in rupees or any currency: see
[Costs and budgets](/kunji/docs/guides/costs-and-budgets/).
