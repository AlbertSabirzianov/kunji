---
title: "FAQ"
description: "Answers to common questions about kunji, the free open-source AI CLI: cost, privacy, supported models, Windows support and more."
sidebar:
  order: 2
---

## Is kunji free?

Yes. kunji is free and open source. You pay the AI providers directly for what you use, at
their normal prices. Ollama models on your own computer cost nothing.

## Do I need an API key?

Yes, from at least one provider, unless you use Ollama. Groq and Google Gemini have free
tiers; see [Quick start](/kunji/docs/getting-started/quickstart/).

## Is it the same as ChatGPT Plus or Claude Pro?

No. Those are monthly subscriptions for the companies' own apps. kunji uses the **API**,
which is billed per use. For many people that's cheaper, and you can use every company's
models from one place.

## Can kunji see my keys or chats?

No. Keys stay in your OS keychain and messages go straight to the provider. See
[Privacy and security](/kunji/docs/concepts/privacy-and-security/).

## Which models can I use?

Any model your providers offer. Run `kunji models <provider>` to see the live list.

## Does it work on Windows?

Yes. Windows is a main platform. Install with `python -m pip install kunji` or use the
standalone `.exe`. macOS and Linux work with pip.

## Can I use it without internet?

Yes, with [Ollama](/kunji/docs/guides/local-models-ollama/) models on your computer.

## Can I switch models in the middle of a chat?

Yes: `/model provider:model`. The conversation carries over.

## How do I see what I've spent?

`kunji usage`, or `/cost` inside a chat. Set limits with `kunji budget set`. See
[Costs and budgets](/kunji/docs/guides/costs-and-budgets/).

## Where are my chats saved?

On your computer only. See [Chat history](/kunji/docs/guides/chat-history/).

## Can I use kunji in scripts or CI?

Yes. Use `kunji ask`, `--raw` output and environment variables for keys. See
[Pipes and scripts](/kunji/docs/guides/pipes-and-scripts/).

## Will there be paid features?

Everything that runs on your computer stays free. Optional paid cloud features (like syncing
across devices or team keys) may come later, clearly separate.

## What does "kunji" mean?

कुंजी (kunji) is Hindi for "key". You bring your own keys; kunji opens every model with them.
