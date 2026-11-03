---
title: "Pipes and scripts"
description: "Use kunji in scripts and pipelines. Pipe command output to an AI model, get plain-text answers and add keys without prompts."
sidebar:
  order: 8
---

`kunji ask` answers one question and exits, which makes it easy to use with other commands.

## Pipe output into a model

```bash
npm test 2>&1 | kunji ask "Why are these tests failing?"
git log --oneline -20 | kunji ask "Write release notes from these commits"
cat config.yaml | kunji ask "Is anything wrong with this config?"
```

Piped text is added under your question. Very large input is cut to the last 200,000
characters.

## Plain output for scripts

When the output goes to a file or another command, kunji prints plain text with no colours or
boxes. Force it with `--raw`:

```bash
kunji ask --raw "Write a .gitignore for a Node project" > .gitignore
git commit -m "$(kunji @commit --raw)"
```

## Keys without prompts

In CI or on servers, use environment variables instead of the keychain:

```bash
export OPENAI_API_KEY=sk-...
kunji ask -m openai:gpt-4o-mini "Summarize this" < report.txt
```

Or store a key from a script without typing it:

```bash
echo "$GROQ_API_KEY" | kunji keys add groq --key-stdin --model llama-3.3-70b-versatile
```

All variables: [Environment variables](/kunji/docs/reference/environment-variables/).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Something failed (bad key, provider error, missing file); the message says why |
| 2 | The command was used wrongly (missing argument, interactive command without a terminal) |
| 130 | Cancelled with Ctrl+C |

## Interactive vs. non-interactive

`kunji chat` and the menu need a real terminal. In scripts, use `kunji ask`, `kunji @name` and
commands with flags (for example `kunji keys remove groq --yes`).
