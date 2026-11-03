"""Saved conversations. Stored only on this computer, in the data folder (`chats/`).

Turn off with:  kunji config set chat.history false
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from kunji.config import atomic_write, data_dir


class HistoryError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


@dataclass
class ChatRecord:
    id: str
    model: str
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    title: str = ""
    system: str = ""
    messages: list[dict] = field(default_factory=list)  # [{"role": "user", "content": "…"}]

    @property
    def turns(self) -> int:
        return sum(1 for m in self.messages if m.get("role") == "user")


def chats_dir() -> Path:
    return data_dir() / "chats"


def new_record(model: str, system: str = "") -> ChatRecord:
    while True:
        chat_id = secrets.token_hex(3)
        if not (chats_dir() / f"{chat_id}.json").exists():
            return ChatRecord(id=chat_id, model=model, system=system)


def make_title(text: str, limit: int = 60) -> str:
    line = " ".join(text.split())
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def save(record: ChatRecord) -> None:
    record.updated = time.time()
    if not record.title:
        first = next((m["content"] for m in record.messages if m.get("role") == "user"), "")
        record.title = make_title(first) or "Untitled chat"
    atomic_write(chats_dir() / f"{record.id}.json",
                 json.dumps(asdict(record), ensure_ascii=False).encode("utf-8"))


def _read(path: Path) -> ChatRecord | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ChatRecord(**{k: data[k] for k in ChatRecord.__dataclass_fields__ if k in data})
    except (OSError, ValueError, TypeError, KeyError):
        return None


def list_all() -> list[ChatRecord]:
    folder = chats_dir()
    if not folder.is_dir():
        return []
    records = [r for p in folder.glob("*.json") if (r := _read(p))]
    return sorted(records, key=lambda r: r.updated, reverse=True)


def latest() -> ChatRecord | None:
    records = list_all()
    return records[0] if records else None


def find(prefix: str) -> ChatRecord:
    prefix = prefix.strip().lower()
    if not prefix:
        raise HistoryError("Which chat?", hint="See ids with: kunji history")
    matches = [r for r in list_all() if r.id.startswith(prefix)]
    if not matches:
        raise HistoryError(f"No saved chat with id {prefix}.", hint="See ids with: kunji history")
    if len(matches) > 1:
        raise HistoryError(f"More than one chat starts with {prefix}.",
                           hint="Type more characters.")
    return matches[0]


@dataclass
class Hit:
    record: ChatRecord
    snippet: str


def search(text: str, limit: int = 30) -> list[Hit]:
    needle = text.strip().lower()
    if not needle:
        return []
    hits: list[Hit] = []
    for record in list_all():
        snippet = ""
        if needle in record.title.lower():
            snippet = record.title
        else:
            for m in record.messages:
                content = str(m.get("content", ""))
                pos = content.lower().find(needle)
                if pos != -1:
                    start = max(0, pos - 30)
                    snippet = ("…" if start else "") + " ".join(
                        content[start:pos + len(needle) + 40].split()) + "…"
                    break
        if snippet:
            hits.append(Hit(record, snippet))
        if len(hits) >= limit:
            break
    return hits


def delete(chat_id: str) -> ChatRecord:
    record = find(chat_id)
    (chats_dir() / f"{record.id}.json").unlink(missing_ok=True)
    return record


def delete_all() -> int:
    count = 0
    folder = chats_dir()
    if folder.is_dir():
        for path in folder.glob("*.json"):
            path.unlink(missing_ok=True)
            count += 1
    return count


def to_markdown(record: ChatRecord) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(record.created))
    lines = [f"# {record.title}", "", f"{record.model} · {stamp} · id {record.id}", ""]
    for m in record.messages:
        who = "You" if m.get("role") == "user" else "Assistant"
        lines += [f"## {who}", "", str(m.get("content", "")), ""]
    return "\n".join(lines)
