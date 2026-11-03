---
title: "How costs are calculated"
description: "How kunji works out the cost of each AI answer from token counts and public price lists, and how accurate it is."
sidebar:
  order: 2
---

AI providers charge per **token**: roughly ¾ of a word. You pay for the tokens you send
(**input**: your message plus the conversation so far) and the tokens you get back
(**output**: the answer).

## The formula

```
cost = input tokens × input price + output tokens × output price
```

Prices are per million tokens, in US dollars, then converted to your
[display currency](/kunji/docs/guides/costs-and-budgets/).

## Where token counts come from

Most providers tell kunji exactly how many tokens each answer used. When one doesn't, kunji
estimates (about 4 characters per token) and marks the numbers with `~`.

## Where prices come from

kunji looks for a price in this order and uses the first it finds:

1. **Your own price** in `config.toml` (`[pricing."provider:model"]`)
2. **kunji's curated list** in the project repository
3. **OpenRouter's public model list**, matched to your model's name

Lists are downloaded at most once a day and cached. If no price is found, the cost shows as `—`.

## Why chats get more expensive

Each message sends the **whole conversation so far** as input, so long chats cost more per
message. Start a fresh one with `/new` when you change topic.

## How accurate is it?

Usually close, but it's an estimate: prices change, some providers charge differently for
cached input or long contexts, and name matching can miss. Your provider's billing page is the
real number.
