---
title: "Chatting"
description: "How to chat with AI models in kunji, write multi-line messages, stop answers, use slash commands and set a system prompt."
sidebar:
  order: 1
---

Start a chat from the menu (**Start a new chat**) or with:

```bash
kunji chat
```

Type your message and press **Enter**. The answer streams in as it's written, then a grey line
shows the model, tokens, cost and time:

```
› what is the difference between a process and a thread?
  A process is a running program with its own memory. A thread is a path of
  execution inside a process; threads of the same process share memory…
  claude-sonnet · 21 in · 148 out · $0.0023 · 2.1s
```

## Writing messages

| Key | Action |
| --- | --- |
| Enter | Send |
| Alt+Enter or Ctrl+J | New line (for longer messages or pasted code) |
| ↑ / ↓ | Bring back a message you typed earlier |
| Tab | Complete commands, model names, prompt names and file paths |
| Ctrl+C | Stop the answer that's being written (what's written so far is kept) |
| Ctrl+D | Leave the chat |

## Slash commands

Type `/` to see them all. The most useful ones:

| Command | What it does |
| --- | --- |
| `/model provider:model` | Switch model, keep the conversation ([more](/kunji/docs/guides/models/)) |
| `/file app.py` | Attach a file to your next message ([more](/kunji/docs/guides/attach-files/)) |
| `@explain …` | Use a saved prompt ([more](/kunji/docs/guides/saved-prompts/)) |
| `/cost` | What this chat and today have cost |
| `/retry` | Get a new answer to your last message |
| `/new` | Start a fresh conversation |
| `/save notes.md` | Export the chat as Markdown |

Full list: [Chat commands](/kunji/docs/reference/chat-commands/).

## System prompts

A system prompt sets how the model should behave for the whole chat.

```bash
kunji chat -s "You are a senior Python developer. Be concise."
```

Inside a chat: `/system Answer in Hindi.` and `/system off` to clear it. To use one for every
new chat, set it in **Settings → Default system prompt** or:

```bash
kunji config set chat.system_prompt "Be concise."
```

## Starting a chat with a specific model

```bash
kunji chat -m openai:gpt-4o-mini
```

Models are written as `provider:model`. See [Switch and pick models](/kunji/docs/guides/models/).

## Continuing later

Chats are saved automatically. Continue the last one with `kunji chat -c`, or pick any saved
chat; see [Chat history](/kunji/docs/guides/chat-history/).

## One-off questions

For a single question without opening a chat, use `kunji ask`:

```bash
kunji ask "How do I undo the last git commit?"
```

See [Pipes and scripts](/kunji/docs/guides/pipes-and-scripts/).
