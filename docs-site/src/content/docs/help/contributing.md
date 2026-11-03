---
title: "Contributing"
description: "How to report bugs, suggest features, improve the docs and contribute code to kunji."
sidebar:
  order: 4
---

kunji is open source and contributions are welcome.

## Report a bug or suggest an idea

[Open an issue](https://github.com/testwithsuraj/kunji/issues/new/choose). For bugs, include
the output of `kunji doctor` and `kunji version`, and **never paste API keys**.

Security problems: report them privately through
[GitHub security advisories](https://github.com/testwithsuraj/kunji/security/advisories/new).

## Improve the docs

Every page has an **Edit page** link at the bottom that opens the file on GitHub. Pages are
Markdown files in `docs-site/src/content/docs/`.

The command reference, provider pages, chat commands, environment variables and changelog
are generated from kunji's code by `scripts/gen_docs.py`, so change the code (or the script),
not those pages.

Run the docs locally:

```bash
python -m pip install -e .
python scripts/gen_docs.py
cd docs-site
npm ci
npm run dev
```

## Contribute code

```bash
git clone https://github.com/testwithsuraj/kunji
cd kunji
python -m pip install -e ".[dev]"
ruff check src tests
pytest
```

Read [CONTRIBUTING.md](https://github.com/testwithsuraj/kunji/blob/main/CONTRIBUTING.md) for
the full guidelines.
