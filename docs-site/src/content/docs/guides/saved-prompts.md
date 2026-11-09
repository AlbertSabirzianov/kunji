---
title: "Saved prompts"
description: "Use kunji's saved prompts like @commit, @explain and @review, and create your own reusable AI prompts for the terminal."
sidebar:
  order: 3
---

Saved prompts are instructions you use often, saved under a short name. Run them with `@name`.

```bash
kunji @commit                                # write a commit message
kunji @explain "TypeError: x is undefined"   # explain an error
git diff | kunji @review                     # review changes
```

## Built-in prompts

| Prompt | What it does |
| --- | --- |
| `@commit` | Writes a git commit message from your staged changes (or unstaged, if nothing is staged) |
| `@explain` | Explains code, an error or a concept in plain language |
| `@review` | Reviews code for bugs, security issues and readability |
| `@fix` | Finds the bug and shows corrected code |
| `@summarize` | Summarizes text in 3–7 bullet points |
| `@translate` | Translates text; start with `to Hindi:` (or any language) to choose |
| `@shell` | Explains a shell command part by part and warns if it is destructive |

## Giving prompts something to work on

Anything you type after the name, anything you pipe in, and any files you attach with `-f`
are all passed to the prompt:

```bash
kunji @explain "what does async/await do?"
cat error.log | kunji @explain
kunji @fix -f src/app.py
kunji @summarize -f meeting-notes.txt
kunji @translate "to Hindi: see you tomorrow"
```

Use `-m` to run a prompt with a different model: `kunji @review -m openai:gpt-4o -f app.py`.

## Writing commit messages with @commit

Inside a git project:

```bash
git add .
kunji @commit
```

kunji runs `git diff --staged` on your computer and asks the model for a short commit message
(a subject line plus a short body). Copy it into your commit, or save it straight away:

```bash
git commit -m "$(kunji @commit --raw)"
```

## Using prompts inside a chat

Start a message with `@name`:

```
› @explain this regex: ^[\w.+-]+@\w+\.\w+$
```

Type `@` and press **Tab** to see prompt names. `/prompts` lists them all. To send a message
that really starts with `@`, type `@@`.

## Create your own

From the menu: **Run a saved prompt → Create a new prompt…**

Or in one line:

```bash
kunji prompts add standup -t "Turn these notes into a short standup update: {input}" -d "Standup update"
kunji @standup "fixed login bug, started on payments"
```

Without `-t`, `kunji prompts add standup` opens your text editor.

### Placeholders

| Placeholder | Replaced with |
| --- | --- |
| `{input}` | The text you give, plus piped input and attached files |
| `{git_diff}` | Your staged git changes (or unstaged ones if nothing is staged) |

If your prompt has no `{input}`, your text is added at the end.

## Manage prompts

```bash
kunji prompts                  # list
kunji prompts show review      # see a prompt's text
kunji prompts edit explain     # change one (editing a built-in saves your own copy)
kunji prompts remove standup   # delete yours
kunji prompts path             # folder where your prompts are stored
```

Your prompts are plain Markdown files in that folder, so you can edit them with any editor,
back them up or share them. A file with a built-in's name replaces the built-in; delete it to
get the original back.
