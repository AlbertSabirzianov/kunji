---
title: "The menu"
description: "Run kunji with no command to open an arrow-key menu for chatting, prompts, saved chats, models, providers, budgets and settings."
sidebar:
  order: 3
---

Run `kunji` on its own and you get a menu. It stays open until you choose **Exit**, so you
can chat, change a setting, chat again, all without typing commands.

```
 kunji   your keys · every model · one terminal
┌──────────────────────────────────────────────────────────────────┐
│  Default model         Provider     Providers    Today    State  │
│──────────────────────────────────────────────────────────────────│
│  claude-sonnet         anthropic    2            $0.12    READY  │
└──────────────────────────────────────────────────────────────────┘
◆ What would you like to do?
 ❯ Start a new chat          anthropic:claude-sonnet
   Continue last chat        fix the login bug
   Open a saved chat
   Run a saved prompt        @explain, @commit, …
   Compare models
   Change default model
   Providers and keys
   Usage and budgets
   Settings
   Check setup (doctor)
   Exit
```

## Moving around

| Key | Action |
| --- | --- |
| ↑ / ↓ | Move |
| Enter | Choose |
| Ctrl+C | Go back one step (or leave the menu from the top level) |

## What each item does

| Item | What happens |
| --- | --- |
| Start a new chat | Opens a chat with your default model. Leaving the chat brings you back here. |
| Continue last chat | Reopens your most recent saved chat with its full conversation. |
| Open a saved chat | Pick any saved chat to continue, show, export or delete. You can search too. |
| Run a saved prompt | Pick a prompt like `@explain`, type your text, optionally attach a file. |
| Compare models | Type a prompt, tick the models with Space, and see their answers side by side. |
| Change default model | Pick a provider, then search its live model list. |
| Providers and keys | Add or replace keys, test them, remove a provider, add a custom server. |
| Usage and budgets | Usage for the week or month, and daily spending limits. |
| Settings | Currency, chat history on/off, default system prompt, update checks. |
| Check setup (doctor) | Checks Python, the keychain and your providers. |
| Upgrade kunji | Appears only when a new version is out. |

## First run

If you haven't added a provider yet, the menu starts by asking which provider you want, then
for your key. Press Ctrl+C to skip and go to the menu.

## Menu or commands?

Everything in the menu is also a command, and commands are better for scripts and speed.
For example, **Compare models** is the same as `kunji compare "…"`. See the
[command reference](/kunji/docs/reference/cli/).
