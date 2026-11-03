# Privacy

Short version: **your keys and prompts go only to the AI provider you chose.** Kunji has no
servers in the path of your conversations.

## What leaves your machine

| Request | When | What is sent | Turn off |
| --- | --- | --- | --- |
| Your provider's API | When you chat, ask, compare, list models | Your prompt + your key, to that provider only | — |
| `pypi.org/pypi/kunji/json` | At most once a day | Nothing about you (plain GET) | `kunji config set updates.check false` |
| `openrouter.ai/api/v1/models` | At most once a day | Nothing about you (plain GET, public price list) | `kunji config set network.catalog false` |
| `raw.githubusercontent.com/…/catalog/pricing.json` | At most once a day | Nothing about you | `kunji config set network.catalog false` |
| kunji cloud check-in | **Only if you set `cloud.url`** | Random install id, kunji version, OS name, license key if you have one | `kunji config set cloud.checkin false` |

Kunji never sends API keys, prompts, answers, file contents or usage history to any kunji
server.

## What stays on your machine

- API keys — in your OS keychain.
- Settings, usage ledger, chat input history, caches — in your user folders
  (`kunji config path`). Delete them any time.
- Saved chats — in `data/chats/` (one file per chat). Delete with `kunji history delete`,
  or stop saving with `kunji config set chat.history false`.
- Your saved prompts — Markdown files in the `prompts` folder (`kunji prompts path`).
- Files you attach with `/file` or `-f` are read locally and sent only to the provider you
  are chatting with. `@commit` runs `git diff` on your computer; nothing else is executed.

## The install id

A random UUID created on first use (`data/install_id`). It is not derived from your
hardware or account and can be deleted at any time; a new one is created.
