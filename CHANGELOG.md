# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-02

### Added
- Interactive chat with streaming markdown answers, slash commands and history.
- Providers: OpenAI, Anthropic, Gemini, Groq, OpenRouter, DeepSeek, Mistral, xAI, Together,
  Ollama, and custom OpenAI-compatible servers.
- `/model` switching mid-conversation with tab completion.
- API keys in the OS keychain (or environment variables), verified before saving.
- Live cost meter, `kunji usage`, and daily budgets (warn at 80%, block at 100%).
- `kunji compare` — one prompt, several models, with fastest/cheapest summary.
- Automatic fallback to the next model on rate limits or outages.
- `kunji ask` with pipe support and `--raw` output for scripts.
- `kunji doctor`, `kunji models`, `kunji providers`, `kunji config`.
- Responsive, minimal theme that adapts to any terminal width.
- Update notice via PyPI and signed (Ed25519) cloud check-in client (off until a server URL
  is configured).
