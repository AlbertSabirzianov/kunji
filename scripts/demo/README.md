# Demo recordings

Re-creates the GIFs and videos in `assets/` from the **real kunji CLI**. The AI answers come
from `mock_server.py` on `127.0.0.1:8765`, so no API key, no network and no cost.

```bash
python -m pip install -e ".[dev]" pyte    # from the repo root
bash scripts/demo/build.sh                # all scenes (~5 min)
bash scripts/demo/build.sh compare        # one scene
```

Also needs `ffmpeg` and `node`. Linux or macOS only (it uses a pseudo-terminal).

| File | What it does |
| --- | --- |
| `scenes.py` | The scripts: what to type and when (`demo`, `compare`, `commit`, `budget`) |
| `record.py` | Runs a scene in a pseudo-terminal and saves an asciicast (`.cast`) |
| `render.mjs` | Plays the `.cast` in xterm.js in headless Chromium and saves PNG frames |
| `build.sh` | Record → render → MP4 (30 fps, 2×) and GIF (12 fps, optimised) |
| `mock_server.py` | Fake OpenAI- and Anthropic-style streaming API with canned answers |
| `setup_home.py` | Throwaway `KUNJI_HOME` with providers pointed at the mock server |
| `demo_keyring.py` | In-memory keyring so the header says "keychain" without a real one |
| `social_preview.mjs` | `assets/social-preview.png` for GitHub (1280×640) |

To change an answer, edit `ANSWERS` in `mock_server.py`. To change timing or steps, edit
`scenes.py`. Re-record after UI changes so the README never shows an old design.
