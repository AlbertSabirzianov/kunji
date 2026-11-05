# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added
- Documentation site at https://testwithsuraj.github.io/kunji/docs/ with guides, provider
  setup pages, a full command reference generated from the code, troubleshooting and FAQ.
- New website: interactive terminal demos (chat, switch model, compare, @commit, budget),
  a Features page, light/dark theme (shared with the docs), Hindi pages and a mobile menu.
- Demo GIF and videos in the README, recorded from the real CLI (`scripts/demo/`).
- How-to guides in the docs: Claude in the terminal, a free AI CLI for Windows, the Groq API
  from the command line, ChatGPT API vs Plus cost, and AI commit messages.

### Fixed
- The end of a chat said "1 replies"; it now says "1 reply".

## [0.1.2] - 2026-11-04

First release with these features (0.1.1 was built but never published).

### Added
- **A menu, so you don't have to remember commands.** Run `kunji` and pick what you want
  with the arrow keys: chat, saved chats, prompts, compare, models, providers, usage,
  budgets and settings. It stays open until you choose Exit, and leaving a chat brings you
  back to it. First time? It starts by helping you add a provider.
- **Saved prompts.** Ready-made instructions you run in one word:
  `kunji @commit` writes a commit message from your staged git changes, and `@explain`,
  `@review`, `@fix`, `@summarize` and `@translate` are built in. Use them inside a chat too
  (`@explain this error …`), or create your own with `kunji prompts add`.
- **Chats you can come back to.** Every chat is saved on your computer.
  `kunji chat -c` continues the last one, `kunji history` lists them all, and
  `kunji history search` finds old answers.
- **Attach files.** `/file app.py` in a chat (Tab completes the path), or
  `kunji ask -f app.py "what does this do?"`. Text files up to 200 KB each.
- **Upgrade notices and `kunji upgrade`.** When a new version is out, kunji tells you at
  startup and upgrades itself with one command.
- **Website** at https://testwithsuraj.github.io/kunji/ with install steps, privacy policy
  and terms.

### Changed
- Install instructions use `pip install kunji` everywhere.
- Saved-chat titles use what you typed, not the expanded prompt.

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

### Build
- Standalone downloads for Windows (`kunji-windows-x64.exe`) and Linux; macOS users install
  with `pipx install kunji` (a macOS download can be switched on later).
- Releases run automatically when the version number changes, with notes taken from this
  changelog.

### Design
- Compact one-row summary tables (`Strip`) for the chat header, `/cost`, `keys add`,
  `usage` totals and `version` — 5 lines instead of ~11, more room for the conversation.
- `kunji compare` summary is now a table: time, tokens, cost and fastest/cheapest badges
  for every model.
- README badges restyled for readability on light and dark GitHub themes.
