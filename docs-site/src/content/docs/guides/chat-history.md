---
title: "Chat history"
description: "kunji saves your AI chats on your computer. Continue, search, export and delete past conversations."
sidebar:
  order: 4
---

Every chat is saved automatically on your computer, after each answer. Nothing is uploaded.

## Continue a chat

```bash
kunji chat -c                  # continue your most recent chat
kunji chat --resume 3fa2c1     # continue a specific one
```

From the menu: **Continue last chat**, or **Open a saved chat** to pick one. When a chat
reopens, kunji shows its title and the last answer so you know where you were, and uses the
same model as before (pass `-m` to switch).

When you leave a chat, kunji prints its id:

```
Saved as chat 3fa2c1. Continue later: kunji chat --resume 3fa2c1
```

You only need the first few characters of an id.

## List and search

```bash
kunji history                  # newest first
kunji history search docker    # find chats by words in titles or messages
```

Inside a chat: `/history` shows recent chats and `/history docker` searches.

## Show, export and delete

```bash
kunji history show 3fa2c1
kunji history export 3fa2c1            # writes kunji-chat-3fa2c1.md
kunji history export 3fa2c1 -o notes.md
kunji history delete 3fa2c1
kunji history delete --all             # asks before deleting everything
```

## Turn history off

```bash
kunji config set chat.history false
```

Or **Settings → Save chat history** in the menu. Existing chats are kept until you delete
them.

## Where chats are stored

One JSON file per chat in the `chats` folder of kunji's data folder; run `kunji config path`
to see where. See [Files and folders](/kunji/docs/reference/files/).
