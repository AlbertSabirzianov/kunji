"""Drive a real kunji session in a pseudo-terminal and save it as an asciicast v2 file.

    python scripts/demo/record.py <scene> out.cast

Scenes are defined in scenes.py. Keystrokes are typed with human-like delays.
"""

from __future__ import annotations

import fcntl
import json
import os
import pty
import re
import select
import struct
import sys
import termios
import time

import pyte
from scenes import SCENES

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Z0-9]|\x1b[=>]")


class Session:
    def __init__(self, argv: list[str], cols: int, rows: int, env: dict, out_path: str):
        self.cols, self.rows = cols, rows
        self.events: list[tuple[float, str, str]] = []
        self.buffer = ""
        pid, fd = pty.fork()
        if pid == 0:
            os.execvpe(argv[0], argv, env)  # noqa: S606 (fixed demo command)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.start = time.monotonic()
        self.out_path = out_path
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)

    def _pump(self, timeout: float) -> bool:
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return True
        try:
            data = os.read(self.fd, 65536)
        except OSError:
            return False
        if not data:
            return False
        text = data.decode("utf-8", "replace")
        self.events.append((time.monotonic() - self.start, "o", text))
        self.stream.feed(text)
        if "\x1b[6n" in text:  # cursor position request (prompt_toolkit asks for it)
            row, col = self.screen.cursor.y + 1, self.screen.cursor.x + 1
            os.write(self.fd, f"\x1b[{row};{col}R".encode())
        self.buffer += ANSI.sub("", text)
        self.buffer = self.buffer[-20000:]
        return True

    def pause(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if not self._pump(max(0.0, min(0.05, end - time.monotonic()))):
                return

    def wait(self, pattern: str, timeout: float = 20.0) -> None:
        end = time.monotonic() + timeout
        mark = len(self.buffer)
        while time.monotonic() < end:
            if re.search(pattern, self.buffer[max(0, mark - 2000):]):
                return
            if not self._pump(0.05):
                break
        raise SystemExit(f"timed out waiting for {pattern!r}; tail:\n{self.buffer[-800:]}")

    def send(self, data: str) -> None:
        os.write(self.fd, data.encode())
        self.pause(0.02)

    def type(self, text: str, cps: float = 18.0) -> None:
        for ch in text:
            self.send(ch)
            self.pause(1.0 / cps)

    def finish(self) -> None:
        self.pause(0.3)
        try:
            os.kill(self.pid, 9)
        except ProcessLookupError:
            pass
        header = {"version": 2, "width": self.cols, "height": self.rows,
                  "env": {"TERM": "xterm-256color"}}
        with open(self.out_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(header) + "\n")
            for t, kind, data in self.events:
                fh.write(json.dumps([round(t, 4), kind, data]) + "\n")


def main() -> None:
    scene_name, out_path = sys.argv[1], sys.argv[2]
    scene = SCENES[scene_name]
    env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor",
               COLUMNS=str(scene["cols"]), LINES=str(scene["rows"]))
    env.pop("NO_COLOR", None)
    session = Session(scene.get("argv", ["bash", "--norc", "--noprofile", "-i"]),
                      scene["cols"], scene["rows"], env, out_path)
    scene["run"](session)
    session.finish()


if __name__ == "__main__":
    main()
