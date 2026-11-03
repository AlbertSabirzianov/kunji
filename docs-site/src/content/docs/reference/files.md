---
title: "Files and folders"
description: "Where kunji stores its settings, saved chats, prompts, usage history and caches on Windows, macOS and Linux."
sidebar:
  order: 50
---

Run `kunji config path` to see the exact folders on your computer.

## Default locations

| | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Settings | `%LOCALAPPDATA%\kunji` | `~/Library/Application Support/kunji` | `~/.config/kunji` |
| Data | `%LOCALAPPDATA%\kunji` | `~/Library/Application Support/kunji` | `~/.local/share/kunji` |
| Cache | `%LOCALAPPDATA%\kunji\Cache` | `~/Library/Caches/kunji` | `~/.cache/kunji` |

Set `KUNJI_HOME` to keep everything in one folder instead (with `config`, `data` and `cache`
inside it).

## What's inside

| File | Folder | What it is |
| --- | --- | --- |
| `config.toml` | Settings | Your settings (no keys) |
| `prompts/*.md` | Settings | Your saved prompts |
| `chats/*.json` | Data | Saved chats, one file each |
| `usage.jsonl` | Data | Tokens and cost of every request |
| `history.txt` | Data | Messages you typed, for ↑ in chats |
| `install_id` | Data | A random id (not linked to you or your hardware) |
| `*_prices.json`, `models_*.json`, `update.json` | Cache | Price lists, model lists, version check; safe to delete |

**API keys are not in any of these files.** They're in your OS keychain (Windows Credential
Manager, macOS Keychain or Linux Secret Service), under the name `kunji`.

## Start fresh

1. Remove keys: `kunji keys remove <provider>` for each provider.
2. Delete the folders above.

Or on Windows:

```bash
rmdir /s /q "%LOCALAPPDATA%\kunji"
```
