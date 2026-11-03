---
title: "What is kunji?"
description: "kunji is a free, open-source terminal app for chatting with any AI model using your own API keys, with a live cost meter and daily budgets."
---

**kunji** is a free, open-source app for your terminal that lets you chat with AI models from
many companies, using **your own API keys**. You pay each provider directly. kunji never sees
your bill, your keys or your conversations.

*Kunji (कुंजी) means "key" in Hindi.*

## What you can do with it

- **Chat with any model** from OpenAI, Anthropic, Google, Groq, OpenRouter, DeepSeek, Mistral,
  xAI, Together AI, or a model running on your own computer with Ollama.
- **Switch models in the middle of a conversation.** Ask GPT, then ask Claude the same thing,
  without starting over.
- **See what every answer costs**, and set daily budgets so you never get a surprise bill.
- **Compare models side by side** to find the fastest or cheapest one for a task.
- **Save time with prompts** like `kunji @commit`, which writes a git commit message from your
  changes.
- **Come back to old chats**, attach files, and pipe the output of any command into a model.

## Who it's for

kunji is for developers and anyone comfortable with a terminal who already uses AI tools and
wants one clean place for all of them: no browser tabs, no copy-paste, no separate app per
company.

## How it works

```
you ──► kunji (on your computer) ──► the AI provider you choose
          │
          └── keys in your OS keychain, history and costs in local files
```

There is no kunji server in the middle. Your API key and your messages go straight from your
computer to the provider. Read more in [Privacy and security](/kunji/docs/concepts/privacy-and-security/).

## Free and open source

Everything that runs on your computer is free and open source under the
[Apache-2.0 licence](https://github.com/testwithsuraj/kunji/blob/main/LICENSE), forever.

## Next steps

1. [Install kunji](/kunji/docs/getting-started/installation/)
2. [Have your first chat](/kunji/docs/getting-started/quickstart/)
3. [Learn the menu](/kunji/docs/getting-started/menu/)
