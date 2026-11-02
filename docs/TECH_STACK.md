# Tech stack

| Area | Choice | Why |
| --- | --- | --- |
| Language | Python 3.11+ | Easy to contribute to; `tomllib` built in |
| Output UI | [Rich](https://github.com/Textualize/rich) | Panels, tables, live rendering, markdown |
| Chat input | [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) | Multi-line input, history, completion, resize-safe |
| Pickers | [questionary](https://github.com/tmbo/questionary) | Arrow-key selects, masked password input |
| Commands | [Typer](https://github.com/fastapi/typer) | Typed commands, generated help |
| HTTP | [httpx](https://www.python-httpx.org/) | Streaming, timeouts, easy mocking in tests |
| Secrets | [keyring](https://github.com/jaraco/keyring) | OS credential stores on every platform |
| Paths | [platformdirs](https://github.com/tox-dev/platformdirs) | Correct config/data/cache folders per OS |
| Config | TOML (`tomllib` + [tomli-w](https://github.com/hukkin/tomli-w)) | Human-editable |
| Signatures | [cryptography](https://cryptography.io/) | Ed25519 verification of cloud replies |
| Build | [hatchling](https://hatch.pypa.io/) | Simple `pyproject.toml` builds |
| Binaries | [PyInstaller](https://pyinstaller.org/) | Single-file executables for winget/Scoop/Homebrew |
| Lint/format | [Ruff](https://docs.astral.sh/ruff/) | Fast, one tool |
| Tests | [pytest](https://pytest.org/) + `httpx.MockTransport` | No real network in tests |
| CI/CD | GitHub Actions | Tests on 3 OSes, CodeQL, trusted publishing to PyPI |

Providers are implemented with plain HTTP instead of vendor SDKs. Most providers offer an
OpenAI-compatible endpoint, so two small adapters (`openai_compat.py`, `anthropic.py`) cover
everything and keep installs small and auditable.
