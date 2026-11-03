---
title: "Privacy and security"
description: "How kunji protects your API keys and conversations. Keys stay in your OS keychain and prompts go only to the AI provider you choose."
sidebar:
  order: 1
---

Short version: **your keys and prompts go only to the AI provider you choose.** There is no
kunji server in between.

## Your API keys

- Stored in your operating system's credential store: **Windows Credential Manager**,
  **macOS Keychain** or **Linux Secret Service** (GNOME Keyring or KWallet).
- Never written to a kunji file, and always shown masked (`sk-ant••••••••3f9a`).
- Checked with the provider before saving; a key that's rejected is never stored.
- Sent only to that key's own provider, over HTTPS.
- Removed from any error message before it's shown.

No keychain on your system (for example a server without a desktop)? Use
[environment variables](/kunji/docs/reference/environment-variables/) instead. kunji never
falls back to a plain-text file.

## What leaves your computer

| What | Where it goes | Turn off |
| --- | --- | --- |
| Your messages and the API key | Only to the provider you're chatting with | — |
| Files you attach | Only to that provider | — |
| A version check (no data about you) | PyPI, at most once a day | `kunji config set updates.check false` |
| Price list downloads (no data about you) | OpenRouter and GitHub, at most once a day | `kunji config set network.catalog false` |

kunji does **not** send your keys, prompts, answers, files or usage to the kunji project.
There are no analytics.

## What stays on your computer

Settings, saved chats, saved prompts, usage history and caches; see
[Files and folders](/kunji/docs/reference/files/). Delete them any time.

`@commit` runs `git diff` on your computer to read your changes. kunji runs no other
programs, except `pip` when you choose `kunji upgrade`.

## Plain HTTP warning

For custom servers, kunji allows `http://` only for addresses on your own computer or
network, and warns you about anything else because your key would travel unencrypted.

## Open source

All of this can be checked in the
[source code](https://github.com/testwithsuraj/kunji). Found a security problem? Please
report it privately through
[GitHub security advisories](https://github.com/testwithsuraj/kunji/security/advisories/new).

See also the full [privacy policy](https://testwithsuraj.github.io/kunji/privacy.html).
