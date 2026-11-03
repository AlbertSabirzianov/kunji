"""Attach local text files to a message (`/file` in chat, `-f` on `ask` and `@prompts`).

Files are read on this computer and sent only to the AI provider you are talking to.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 500_000

_LANG = {
    ".py": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".jsx": "jsx", ".json": "json", ".toml": "toml",
    ".yaml": "yaml", ".yml": "yaml", ".md": "markdown", ".html": "html", ".css": "css",
    ".sh": "bash", ".ps1": "powershell", ".bat": "batch", ".go": "go", ".rs": "rust",
    ".java": "java", ".kt": "kotlin", ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp",
    ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".sql": "sql", ".lua": "lua", ".xml": "xml", ".csv": "csv", ".txt": "text", ".log": "text",
    ".sol": "solidity", ".dart": "dart", ".vue": "vue", ".svelte": "svelte",
}


class AttachmentError(Exception):
    pass


@dataclass
class Attachment:
    path: Path
    text: str
    size: int

    @property
    def lang(self) -> str:
        return _LANG.get(self.path.suffix.lower(), "")

    @property
    def display(self) -> str:
        try:
            return str(self.path.relative_to(Path.cwd()))
        except ValueError:
            return str(self.path)


def load(path_str: str) -> Attachment:
    raw = path_str.strip().strip('"').strip("'")
    if not raw:
        raise AttachmentError("No file path given.")
    path = Path(os.path.expandvars(raw)).expanduser()
    if not path.exists():
        raise AttachmentError(f"File not found: {raw}")
    if path.is_dir():
        raise AttachmentError(f"{raw} is a folder. Attach files one by one.")
    path = path.resolve()
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise AttachmentError(
            f"{path.name} is {size // 1000} KB; the limit is {MAX_FILE_BYTES // 1000} KB per file."
        )
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        raise AttachmentError(
            f"{path.name} looks like a binary file. Only text files can be attached."
        )
    return Attachment(path, data.decode("utf-8", errors="replace"), size)


def load_many(paths: list[str]) -> list[Attachment]:
    items = [load(p) for p in paths]
    check_total(items)
    return items


def check_total(items: list[Attachment]) -> None:
    total = sum(a.size for a in items)
    if total > MAX_TOTAL_BYTES:
        raise AttachmentError(
            f"Attached files add up to {total // 1000} KB; "
            f"the limit is {MAX_TOTAL_BYTES // 1000} KB."
        )


def render(items: list[Attachment]) -> str:
    blocks = []
    for a in items:
        fence = "````" if "```" in a.text else "```"
        blocks.append(f"File: {a.display}\n{fence}{a.lang}\n{a.text.rstrip()}\n{fence}")
    return "\n\n".join(blocks)


def with_files(message: str, items: list[Attachment]) -> str:
    if not items:
        return message
    files = render(items)
    return f"{message}\n\n{files}" if message.strip() else files
