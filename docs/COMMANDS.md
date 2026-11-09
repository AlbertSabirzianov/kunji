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
