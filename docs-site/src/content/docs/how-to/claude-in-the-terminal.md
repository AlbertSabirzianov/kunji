---
title: "Use Claude in the terminal"
description: "How to chat with Anthropic's Claude from your terminal on Windows, macOS or Linux with your own API key, see what each answer costs, and pipe files and errors into it."
sidebar:
  order: 1
---

You can talk to Claude from any terminal with your own Anthropic API key. No browser tab, no
monthly plan: you pay Anthropic only for what you use, and you see the cost of every answer.

This guide uses **kunji**, a free open-source terminal app that works with Claude and every
other major AI provider.

## 1. Install kunji

```bash
pip install kunji
```

On Windows, use `python -m pip install kunji`, or download the `.exe` (no Python needed).
See [Install kunji](/kunji/docs/getting-started/installation/) for every option.

## 2. Get an Anthropic API key

1. Open [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) and
   sign in.
2. Add a little credit under **Billing**. The API is billed separately from a Claude.ai
   subscription.
3. Create a key and copy it.

## 3. Add the key to kunji

```bash
kunji keys add anthropic
```

Paste the key when asked. kunji checks it, then saves it in your operating system's keychain
(Windows Credential Manager, macOS Keychain or Secret Service on Linux), never in a plain
text file. Pick a default Claude model from the list it shows.

## 4. Chat with Claude

```bash
kunji chat
```

```
› explain recursion in one line
  A function that solves a problem by calling itself on a smaller piece of it,
  until it reaches a case simple enough to answer directly.
  claude-sonnet-4-5 · 19 in · 33 out · $0.0006 · 0.7s
```

The grey line under each answer shows the model, tokens and what that answer cost.
Type `/` to see chat commands, and press **Ctrl+D** to leave.

Prefer menus? Run `kunji` on its own for an arrow-key menu.

## One-off questions and pipes

```bash
kunji ask "what does chmod 755 mean?"
npm test 2>&1 | kunji ask "why is this failing?"
kunji ask -f app.py "find the bug in this file"
```

Use `-m` to pick a model for one command, for example `-m anthropic:claude-sonnet-4-5`.

## Switch between Claude and other models

Inside a chat, `/model` switches model and keeps the conversation:

```
› /model openai:gpt-4o-mini
✓ Switched to openai:gpt-4o-mini  conversation kept
```

Useful for a second opinion, or to move cheap follow-up questions to a cheaper model.
See [Switch and pick models](/kunji/docs/guides/models/).

## Keep spending under control

```bash
kunji budget set anthropic 2     # daily limit, in your display currency
```

kunji warns at 80% and stops at 100%. See [Costs and budgets](/kunji/docs/guides/costs-and-budgets/).

## Is my data private?

kunji talks to Anthropic directly from your computer. There is no kunji server in between,
so your key, prompts and answers never pass through anyone else. Details:
[Privacy and security](/kunji/docs/concepts/privacy-and-security/).
