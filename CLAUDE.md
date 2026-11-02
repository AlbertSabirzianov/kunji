# Notes for AI coding assistants (and humans)

kunji is a bring-your-own-key AI CLI. Read `docs/ARCHITECTURE.md` first.

## Rules
- Never log, print, store or send API keys. Run provider error text through
  `keystore.redact()`. Keys live only in the OS keychain or env vars.
- No new network calls without updating `docs/PRIVACY.md` and adding an off switch.
- UI: use the components in `src/kunji/ui/components.py`; colours only from
  `ui/theme.py` (hex values, never named colours like "white"). Every screen must work
  from 40 to 200 columns — test with `Console(width=N, record=True)`.
- Don't print a fake shell prompt (like `user@pc ~`) — the real terminal already shows one.
- Tests: `pytest` with `httpx.MockTransport`; never hit real APIs in tests.
- Lint: `ruff check src tests` (line length 100).
- Everything that runs locally stays free and open source. Paid features are server-side
  and live in the private `kunjicloud` repo — don't add licence checks that gate local features.

## Commands
```bash
python -m pip install -e ".[dev]"
ruff check src tests && pytest
KUNJI_HOME=/tmp/kunji-dev kunji
```
