---
title: "Attach files"
description: "Send code, logs and text files to an AI model from the terminal with kunji's /file command and the -f option."
sidebar:
  order: 5
---

Attach text files so the model can read them: code, logs, notes, configs.

## In a chat

```
› /file src/app.py
✓ Attached src/app.py  3.2 KB, sent with your next message
› what does the login function do?
```

- Press **Tab** after `/file ` to complete paths.
- Attach several: `/file app.py utils.py` or repeat `/file`.
- `/file` on its own lists what's attached; `/file clear` removes them.
- Files are sent with your next message only, then cleared.

## From the command line

```bash
kunji ask -f app.py "What does this do?"
kunji ask -f app.py -f test_app.py "Why does this test fail?"
kunji @review -f app.py
```

## Limits

| Limit | Value |
| --- | --- |
| Per file | 200 KB |
| All files in one message | 500 KB |
| File types | Text only (code, logs, Markdown, JSON, CSV…). Binary files like images or PDFs are refused. |

Large files cost more tokens. For long logs, consider sending just the relevant part:

```bash
tail -n 200 server.log | kunji ask "What went wrong?"
```

## Privacy

Files are read on your computer and sent only to the AI provider you're chatting with.
