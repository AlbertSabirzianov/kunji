# kunji command guide

Run `kunji` on its own to open the menu: everything below is also there, no typing
needed. Commands are handy for speed and for scripts. Add `--help` to any command for
all its options.

## Getting started

| Command | What it does |
| --- | --- |
| `kunji` | Open the menu (stays open until you choose Exit) |
| `kunji keys add` | Add a provider: pick one, paste your key, choose a default model |
| `kunji chat` | Start chatting with your default model |
| `kunji doctor` | Check that Python, your keychain and your providers are working |
| `kunji upgrade` | Update kunji to the newest version |

## Chatting

| Command | What it does |
| --- | --- |
| `kunji chat` | New chat |
| `kunji chat -c` | Continue your most recent chat |
| `kunji chat --resume 3fa2c1` | Continue a specific saved chat |
| `kunji chat -m groq:llama-3.3-70b-versatile` | Chat with a specific model |
| `kunji chat -s "Answer in Hindi"` | Chat with a system prompt |
| `kunji ask "What is a closure?"` | One question, one answer, no chat |
| `kunji ask -f app.py "What does this do?"` | Ask about a file |
| `npm test 2>&1 \| kunji ask "Why does this fail?"` | Send any command's output |

### Inside a chat

| Type | What it does |
| --- | --- |
| `/model groq:llama-3.3-70b-versatile` | Switch model; the conversation carries over (Tab completes) |
| `/models` or `/models llama` | List the current provider's models |
| `/file app.py` | Attach a text file to your next message (Tab completes paths) |
| `/file` · `/file clear` | See or remove attached files |
| `@explain this error: …` | Use a saved prompt |
| `/prompts` | List saved prompts |
| `/history` or `/history docker` | Recent chats, or search them |
| `/cost` | What this chat and today have cost |
| `/system You are concise.` | Set the system prompt (`/system off` clears it) |
| `/retry` | Ask again for a new answer |
| `/new` | Start a fresh conversation |
| `/save notes.md` | Export this chat as a Markdown file |
| `/help` | All commands and shortcuts |
| `/exit` or Ctrl+D | Leave the chat (back to the menu if you came from it) |

Keys: Enter sends, Alt+Enter or Ctrl+J adds a new line, ↑ recalls earlier messages,
Ctrl+C stops an answer.

## Saved prompts

| Command | What it does |
| --- | --- |
| `kunji @commit` | Write a commit message from your staged git changes |
| `kunji @explain "…"` | Explain code, an error or a concept |
| `git diff \| kunji @review` | Review changes for bugs and security issues |
| `kunji @fix -f app.py` | Find the bug in a file and show the fix |
| `kunji @summarize -f notes.txt` | Summarize text in a few bullet points |
| `kunji @translate "to Hindi: good morning"` | Translate text |
| `kunji prompts` | List all prompts |
| `kunji prompts add standup` | Create your own (opens your editor) |
| `kunji prompts add standup -t "Turn into a standup update: {input}"` | Create one in a single line |
| `kunji prompts edit explain` | Change a prompt (editing a built-in saves your own copy) |
| `kunji prompts remove standup` | Delete your prompt |

In your own prompts, `{input}` is replaced by the text you give, and `{git_diff}` by your
staged git changes.

## Saved chats

| Command | What it does |
| --- | --- |
| `kunji history` | List saved chats, newest first |
| `kunji history search docker` | Find chats by words in the title or messages |
| `kunji history show 3fa2c1` | Print a chat |
| `kunji history export 3fa2c1` | Save a chat as a Markdown file |
| `kunji history delete 3fa2c1` | Delete one chat (`--all` deletes every chat) |

Chats are stored only on your computer. Stop saving with
`kunji config set chat.history false`.

## Models and providers

| Command | What it does |
| --- | --- |
| `kunji compare "Explain recursion" -m openai:gpt-4o-mini -m groq:llama-3.3-70b-versatile` | Same prompt, several models; shows the fastest and cheapest |
| `kunji models openai` | List a provider's models with prices |
| `kunji use anthropic:claude-sonnet-4-5` | Set your default model |
| `kunji keys list` | Providers with keys (keys are always masked) |
| `kunji keys test` | Check every key still works |
| `kunji keys remove groq` | Delete a key and its settings |
| `kunji providers` | All supported providers |
| `kunji providers add lmstudio --base-url http://localhost:1234/v1 --no-key` | Add your own OpenAI-compatible server (see [Custom providers](CUSTOM_PROVIDERS.md)) |

## Cost and budgets

| Command | What it does |
| --- | --- |
| `kunji usage` | Tokens and cost per model for the last 7 days (`-d 30` for a month) |
| `kunji budget set openai 2` | Daily limit for one provider (warns at 80%, stops at 100%) |
| `kunji budget set all 5` | Daily limit across all providers |
| `kunji budget show` | Today's spend against each limit |
| `kunji budget clear openai` | Remove a limit |

## Settings

| Command | What it does |
| --- | --- |
| `kunji config set display.currency INR` | Show costs in rupees |
| `kunji config set display.usd_rate 84` | Your conversion rate from US dollars |
| `kunji config set fallback '["groq:llama-3.3-70b-versatile"]'` | Model to try when yours is rate-limited |
| `kunji config show` | All settings |
| `kunji config path` | Where kunji keeps its files |
| `kunji version` | Version, latest version and system info |

All settings: [CONFIG.md](CONFIG.md).
