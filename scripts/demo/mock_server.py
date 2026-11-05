"""Local mock AI server for recording kunji demos. No real API is called.

Speaks just enough of the OpenAI chat-completions and Anthropic Messages streaming
formats for kunji. Answers are picked by keywords in the last user message.

    python scripts/demo/mock_server.py 8765
"""

from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ANSWERS = [
    ("recursion", "A function that solves a problem by calling itself on a smaller piece "
                  "of it, until it reaches a case simple enough to answer directly."),
    ("commit", "feat(chat): show cost and token count after every reply  \n  \n"
               "- add meta line with model, tokens, cost and latency  \n"
               "- keep the running total in the chat footer"),
    ("haiku", "Keys stay on my desk,  \nevery model one prompt away,  \nthe bill: two paise."),
    ("regex", "Use `^[\\w.+-]+@[\\w-]+\\.[\\w.]+$`. It covers everyday addresses; for "
              "full RFC 5322 rules, validate by sending a confirmation email instead."),
]
DEFAULT = "Here is a short, clear answer to your question."

# Compare mode: give each model its own answer so the lanes look different.
HAIKU_BY_MODEL = {
    "claude": "Keys stay on my desk,  \nevery model one prompt away,  \nthe bill: two paise.",
    "llama": "One terminal glows,  \nten models wait for my words,  \nI pay what I use.",
    "gpt": "Quiet cursor blinks,  \nmy own key opens each door,  \nno middleman here.",
    "gemini": "Prompt goes out once,  \nanswers race back side by side,  \nfastest one is green.",
}

# Per-model speed so compare mode has a visible winner (seconds per chunk).
SPEED = {"llama": 0.012, "flash": 0.02, "gpt": 0.035, "claude": 0.03, "deepseek": 0.05}


def answer_for(messages: list[dict], model: str = "") -> str:
    last = ""
    for m in messages:
        if m.get("role") == "user":
            c = m.get("content")
            last = c if isinstance(c, str) else json.dumps(c)
    low = last.lower()
    if "haiku" in low:
        for key, text in HAIKU_BY_MODEL.items():
            if key in model:
                return text
    for key, text in ANSWERS:
        if key in low:
            return text
    return DEFAULT


def chunks(text: str, size: int = 3):
    words = text.split(" ")
    for i in range(0, len(words), size):
        piece = " ".join(words[i:i + size])
        yield piece + (" " if i + size < len(words) else "")


def delay_for(model: str) -> float:
    for key, d in SPEED.items():
        if key in model:
            return d
    return 0.03


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep the recording terminal clean
        pass

    def _json(self, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        models = ["gpt-4o-mini", "gpt-4.1", "claude-sonnet-4-5", "claude-haiku-4-5",
                  "llama-3.3-70b-versatile", "gemini-2.5-flash", "deepseek-chat"]
        self._json({"data": [{"id": m} for m in models]})

    def _start_sse(self) -> None:
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()

    def _send(self, data: str, event: str | None = None) -> None:
        out = (f"event: {event}  \n" if event else "") + f"data: {data}  \n  \n"
        self.wfile.write(out.encode())
        self.wfile.flush()

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        model = str(body.get("model", ""))
        text = answer_for(body.get("messages") or [], model)
        tin = 12 + sum(len(str(m.get("content", ""))) for m in body.get("messages") or []) // 4
        tout = max(1, len(text) // 4)
        delay = delay_for(model)
        time.sleep(delay * 12)  # time to first token
        self._start_sse()
        if self.path.endswith("/v1/messages"):
            self._send(json.dumps({"type": "message_start",
                                   "message": {"usage": {"input_tokens": tin}}}), "message_start")
            for piece in chunks(text):
                time.sleep(delay)
                self._send(json.dumps({"type": "content_block_delta",
                                       "delta": {"type": "text_delta", "text": piece}}))
            self._send(json.dumps({"type": "message_delta",
                                   "usage": {"output_tokens": tout}}))
            self._send(json.dumps({"type": "message_stop"}))
        else:
            for piece in chunks(text):
                time.sleep(delay)
                self._send(json.dumps({"choices": [{"delta": {"content": piece}}]}))
            self._send(json.dumps({"choices": [], "usage": {"prompt_tokens": tin,
                                                            "completion_tokens": tout}}))
            self._send("[DONE]")
        self.close_connection = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
