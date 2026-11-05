---
title: "Write git commit messages with AI"
description: "Generate clear git commit messages from your staged changes with one command, using any AI model and your own API key. Works with Claude, GPT, Gemini, Groq and local Ollama models."
sidebar:
  order: 5
---

Writing a good commit message takes a minute you'd rather spend coding. kunji's `@commit`
prompt reads your staged changes and writes a message for you: a short subject line and a
body that explains what changed.

## Set up once

```bash
pip install kunji
kunji keys add groq        # or openai, anthropic, gemini, ollama, …
```

Any provider works. Fast, cheap models are perfect for commit messages; a local Ollama model
costs nothing and keeps your code on your machine.

## Use it

```bash
git add .
kunji @commit
```

```
feat(chat): show cost and token count after every reply

- add meta line with model, tokens, cost and latency
- keep the running total in the chat footer
```

If nothing is staged, `@commit` uses your unstaged changes instead.

## Commit in one step

```bash
git commit -m "$(kunji @commit --raw)"
```

`--raw` prints plain text with no colours or cost line. To review it first, open it in your
editor:

```bash
git commit -e -m "$(kunji @commit --raw)"
```

## Pick a model for commits

```bash
kunji @commit -m groq:llama-3.3-70b-versatile
kunji @commit -m ollama:qwen2.5
```

## Make it match your team's style

`@commit` is a saved prompt, so you can make your own version, for example to always use
[Conventional Commits](https://www.conventionalcommits.org/) or to add a ticket number. See
[Saved prompts → Create your own](/kunji/docs/guides/saved-prompts/).

## Is my code sent anywhere?

Only the diff is sent, and only to the AI provider you chose, directly from your computer.
With Ollama nothing leaves your machine. See
[Privacy and security](/kunji/docs/concepts/privacy-and-security/).
