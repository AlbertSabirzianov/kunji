# Contributing to kunji

Thanks for helping! Small, focused pull requests are the easiest to review.

## Setup

```bash
git clone https://github.com/testwithsuraj/kunji
cd kunji
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
kunji --version
```

Use a throwaway home so you don't touch your real config:

```bash
# macOS/Linux
export KUNJI_HOME=/tmp/kunji-dev
# Windows (PowerShell)
$env:KUNJI_HOME = "$env:TEMP\kunji-dev"
```

## Before opening a pull request

```bash
ruff check src tests
ruff format --check src tests   # or: ruff format src tests
pytest
```

CI runs the same checks on Windows, macOS and Linux.

## Guidelines

- **Never log, print or store API keys.** Use `keystore.redact()` on any provider error text.
- **No new network calls** without discussing them in an issue first, and every one must be
  documented in `docs/PRIVACY.md` and be possible to switch off.
- **Responsive UI.** New screens use the components in `src/kunji/ui/components.py`
  (`Card`, `ResponsiveTable`, `Frame`, `Steps`). Check them at 40, 80 and 140 columns.
- **Colours** come from `ui/theme.py` (explicit hex values). Don't use named colours like
  `"white"` — terminals remap them.
- **Tests** for every new behaviour. Network calls are mocked with `httpx.MockTransport`.
- Keep dependencies minimal. New dependencies need a short justification in the PR.

## Adding a provider

1. If it speaks the OpenAI chat-completions format, add a `ProviderSpec` to
   `providers/registry.py` — that's usually all.
2. Otherwise add a class in `providers/` implementing `list_models()` and `stream()`.
3. Add tests with recorded/mocked streaming responses.
4. Add it to the providers table in `README.md`.

## Commit messages

Short imperative subject (`Add xAI provider`, `Fix budget warning on day change`).

## Contributor licence

By submitting a contribution you agree it is licensed under the project's
[Apache-2.0 licence](LICENSE), and you confirm you have the right to submit it. The project
may ask you to sign a lightweight contributor agreement (CLA) via a bot on your first pull
request.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
