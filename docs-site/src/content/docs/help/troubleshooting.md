---
title: "Troubleshooting"
description: "Fixes for common kunji problems, such as pip not recognized, kunji not recognized, invalid API key, rate limits, keychain errors and Ollama not running."
sidebar:
  order: 1
---

Start with:

```bash
kunji doctor
```

It checks Python, your settings folder, the keychain and your providers, and says what's
wrong.

## Installing

The easiest fix for almost every install problem is the one-line installer. It doesn't need
Python or pip and adds `kunji` to your PATH for you:

- Windows (PowerShell): `irm https://kunji.iamsuraj.me/install.ps1 | iex`
- macOS / Linux: `curl -fsSL https://kunji.iamsuraj.me/install.sh | sh`

### `kunji` isn't found right after the installer

Your terminal was open before the PATH changed. Close it and open a new one. On macOS and
Linux you can also run the `export PATH=…` line the installer printed. The command is
lowercase: `kunji`.

### `Could not find platform independent libraries` or `No module named 'encodings'`

An older kunji, from an earlier `pip install kunji`, runs instead of the one the installer
set up, and the Python it belongs to is broken. See which copies you have:

```bash
where kunji
```

Delete every line that isn't `...\.local\bin\kunji.exe`, for example:

```bash
del "%LOCALAPPDATA%\Programs\Python\Python314\Scripts\kunji.exe"
```

Then run the installer again. It now puts its own copy first on your PATH and warns about
older copies.

### `irm` or `iex` is not recognized

You're in Command Prompt, not PowerShell. Run:
`powershell -ExecutionPolicy ByPass -c "irm https://kunji.iamsuraj.me/install.ps1 | iex"`.

### The installer says it couldn't download uv

Something blocks `astral.sh` (a firewall, proxy or no internet). Try another network, or
install with pip below.

### `'pip' is not recognized` or `Fatal error in launcher`

Your `pip` command points to a Python that's missing or moved. Run pip through Python:

```bash
python -m pip install kunji
```

If `python` isn't found either, try `py -m pip install kunji`, or reinstall Python from
[python.org](https://www.python.org/downloads/) with **"Add python.exe to PATH"** ticked.

### `'kunji' is not recognized`

pip installed kunji but put it in a folder that isn't on your PATH. Use the one-line
installer above, or run it through Python, which always works:

```bash
python -m kunji
```

To fix it for good on Windows, find the folder with `python -m pip show -f kunji` (look for
`Scripts\kunji.exe`) and add that `Scripts` folder to PATH, or reinstall Python with the PATH
box ticked.

### `error: externally-managed-environment` (Linux)

Your system Python is managed by the OS, so pip won't install into it. Use the installer
(`curl -fsSL https://kunji.iamsuraj.me/install.sh | sh`) or `pipx install kunji`.

## Keys and providers

### `rejected the API key (401)`

The key is wrong, expired or has no credit. Create a new key on the provider's site and run
`kunji keys add <provider>` again. Check with `kunji keys test`.

### `rate limit or quota reached (429)`

You've hit the provider's limit or run out of credit. Wait a minute, check your billing on
the provider's site, or set a [fallback model](/docs/guides/fallback/).

### `not found (404)`

The model name is wrong or not available to your account. List real names with
`kunji models <provider>`.

### `No API key found for …`

Add one with `kunji keys add <provider>`, or set the provider's
[environment variable](/docs/reference/environment-variables/).

### `No secure OS keychain is available`

Common on Linux servers without a desktop. Install GNOME Keyring or KWallet, or use
environment variables like `OPENAI_API_KEY`.

### `Could not reach Ollama`

Start Ollama (open the app or run `ollama serve`) and check `ollama list` shows a model.

### `Could not reach …` (any provider)

Check your internet connection, VPN or proxy. If you're behind a company proxy, set
`HTTPS_PROXY`.

## Chatting

### Colours look wrong or boxes are broken

Use **Windows Terminal** instead of the old Command Prompt window, and a font with box
characters (Cascadia Mono is the default). To turn colours off: `set NO_COLOR=1`.

### `Daily budget reached`

You've hit a limit you set. Raise it (`kunji budget set openai 5`) or remove it
(`kunji budget clear openai`).

### Costs show `—`

kunji doesn't know that model's price. See
[When a price is unknown](/docs/guides/costs-and-budgets/#when-a-price-is-unknown).

## Upgrading

### `kunji upgrade` says I'm up to date, but there's a new version

The check is cached for a day. Run the installer again, or `uv tool upgrade kunji`
(pip installs: `python -m pip install --upgrade kunji`).

### Upgrade fails on Windows with a "file in use" error

Close every kunji window and run `kunji upgrade` again from a new terminal.

## Still stuck?

[Open an issue](https://github.com/testwithsuraj/kunji/issues/new/choose) with the output of
`kunji doctor` and `kunji version`. **Never paste your API key.**
