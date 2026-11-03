---
title: "Upgrade kunji"
description: "How to update kunji to the newest version with kunji upgrade or pip, and how update notices work."
sidebar:
  order: 12
---

## Upgrade

```bash
kunji upgrade
```

kunji checks PyPI for the newest version and installs it with the same Python it runs on.

- **Windows:** the upgrade runs in a new window, because Windows can't replace kunji while
  it's open. kunji closes; open it again when the window says **Done**.
- **Standalone `.exe`:** kunji shows the download link for the new version instead.
- `kunji upgrade --check` only checks.

From version 0.1.0, upgrade once with pip (0.1.0 doesn't have `kunji upgrade` yet):

```bash
python -m pip install --upgrade kunji
```

## Update notices

When a new version is out, kunji shows one line when it starts:

```
⬆ kunji 0.1.3 is available (you have 0.1.2). Upgrade: kunji upgrade
```

The menu also gets an **Upgrade kunji** item. kunji checks PyPI at most once a day in the
background, so startup never waits for the internet.

Turn notices off:

```bash
kunji config set updates.check false
```

## What changed?

See the [changelog](/kunji/docs/releases/changelog/) or the
[GitHub releases](https://github.com/testwithsuraj/kunji/releases).

## Version numbers

kunji uses versions like `0.1.2`. The last number goes up for each release (0.1.1, 0.1.2, …
0.1.9), then the middle number goes up (0.2.0).
