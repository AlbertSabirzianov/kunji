---
title: "A free AI command-line tool for Windows"
description: "Use AI models like Gemini, Llama (via Groq) and local Ollama models from Command Prompt or Windows Terminal, for free, with the open-source kunji CLI."
sidebar:
  order: 2
---

kunji is a free, open-source AI app for the Windows terminal. It works in **Windows
Terminal**, **Command Prompt** and **PowerShell**, and you can use it without paying anything
by picking a provider with a free tier or a model that runs on your own PC.

## Install

Open **PowerShell** and run:

```powershell
irm https://kunji.iamsuraj.me/install.ps1 | iex
```

You don't need Python: the installer sets everything up and adds `kunji` to your PATH. Open a
new terminal and type `kunji`. From Command Prompt, use
`powershell -ExecutionPolicy ByPass -c "irm https://kunji.iamsuraj.me/install.ps1 | iex"`.

**Already have Python 3.11+?** `py -m pip install kunji` works too.

**Single file:** download `kunji-windows-x64.exe` from the
[latest release](https://github.com/testwithsuraj/kunji/releases/latest), rename it to
`kunji.exe` and run it from a terminal in that folder.

Then run:

```bash
kunji
```

A menu opens. Use the arrow keys and Enter; you don't need to learn any commands.

## Free ways to use it

| Option | What you need | Notes |
| --- | --- | --- |
| **Google Gemini** | A free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free tier with daily limits |
| **Groq** | A free key from [console.groq.com/keys](https://console.groq.com/keys) | Very fast open models, free tier with rate limits |
| **Ollama** | [Ollama for Windows](https://ollama.com/download) | Models run on your PC: no key, no bill, works offline |

Free tiers and their limits are set by each provider and can change; check their pages.

Add one from the menu (**Providers and keys → Add a provider**) or with a command:

```bash
kunji keys add gemini
kunji keys add groq
kunji keys add ollama
```

Your key is saved in **Windows Credential Manager**, not in a text file.

## What you can do

```bash
kunji chat                                   # chat
kunji ask "how do I find which process uses port 3000?"
kunji ask -f script.ps1 "explain this script"
kunji compare "write a haiku about rain"     # several models side by side
kunji @commit                                # commit message for staged git changes
```

## Make it look right

kunji uses hex colours that look the same in every Windows theme, and it adapts to any window
width. For the best result use **Windows Terminal** (free in the Microsoft Store) with a font
like Cascadia Mono, which is the default.

## Troubleshooting

- **"kunji is not recognized"**: open a new terminal window after installing. If you used
  pip, use the one-line installer above instead, or see
  [Troubleshooting](/docs/help/troubleshooting/).
- **Windows SmartScreen warns about the .exe**: the file is new and not yet widely
  downloaded. You can check it against the checksums on the release page, or use the one-line installer instead.
