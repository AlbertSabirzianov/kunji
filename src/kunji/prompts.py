"""Saved prompts: reusable instructions you run with `kunji @name` or `@name` in chat.

Built-in prompts ship with kunji. Your own live as Markdown files in the `prompts`
folder next to config.toml (see `kunji prompts path`). A file with the same name as a
built-in replaces it.

Template placeholders:
  {input}     the text you type after the name, plus piped input and attached files
  {git_diff}  your staged git changes (or unstaged ones if nothing is staged)
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kunji.config import atomic_write, config_dir

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
MAX_DIFF_CHARS = 120_000


class PromptError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


@dataclass(frozen=True)
class Prompt:
    name: str
    description: str
    template: str
    builtin: bool = False

    @property
    def needs_git(self) -> bool:
        return "{git_diff}" in self.template


BUILTIN: dict[str, Prompt] = {
    p.name: p
    for p in (
        Prompt(
            "commit",
            "Write a commit message for your staged git changes",
            "Write a git commit message for the changes below.\n"
            "Rules: a short imperative subject line (max 72 characters), a blank line, then "
            "a brief body explaining what changed and why if it isn't obvious. Plain text "
            "only, no markdown, no code fences. Reply with the message only.\n\n"
            "{input}\n\n{git_diff}",
            builtin=True,
        ),
        Prompt(
            "explain",
            "Explain code, an error or a concept in plain language",
            "Explain the following clearly and simply. Say what it does, why, and anything "
            "surprising. If it is an error, explain the likely cause and how to fix it.\n\n"
            "{input}",
            builtin=True,
        ),
        Prompt(
            "review",
            "Review code for bugs, security issues and readability",
            "Review this code like a careful senior engineer. List real problems first "
            "(bugs, security, data loss), then smaller improvements. Be specific and show "
            "corrected code where it helps. Skip praise.\n\n{input}",
            builtin=True,
        ),
        Prompt(
            "fix",
            "Find the bug and show the fixed code",
            "Find what is wrong and show the corrected code. Explain the fix in one or two "
            "sentences.\n\n{input}",
            builtin=True,
        ),
        Prompt(
            "summarize",
            "Summarize text in a few bullet points",
            "Summarize the following in 3–7 short bullet points, keeping names, numbers and "
            "decisions.\n\n{input}",
            builtin=True,
        ),
        Prompt(
            "translate",
            "Translate text (start with 'to Hindi:' to choose the language)",
            "Translate the text below. If it starts with an instruction like 'to Hindi:', "
            "translate into that language; otherwise translate into English (or into Hindi "
            "if it is already English). Reply with the translation only.\n\n{input}",
            builtin=True,
        ),
    )
}


def prompts_dir() -> Path:
    return config_dir() / "prompts"


def _parse_file(name: str, text: str) -> Prompt:
    description = ""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            header = text[3:end]
            body = text[end + 4:].lstrip("\n")
            for line in header.splitlines():
                key, _, value = line.partition(":")
                if key.strip().lower() == "description":
                    description = value.strip()
    return Prompt(name, description or "Your prompt", body.strip())


def user_prompts() -> dict[str, Prompt]:
    out: dict[str, Prompt] = {}
    folder = prompts_dir()
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.md")):
        name = path.stem.lower()
        if not NAME_RE.match(name):
            continue
        try:
            out[name] = _parse_file(name, path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return out


def all_prompts() -> dict[str, Prompt]:
    merged = dict(BUILTIN)
    merged.update(user_prompts())
    return dict(sorted(merged.items()))


def get(name: str) -> Prompt:
    name = name.lstrip("@").lower()
    found = all_prompts().get(name)
    if not found:
        raise PromptError(f"No prompt named @{name}.", hint="See them all with: kunji prompts")
    return found


def path_for(name: str) -> Path:
    return prompts_dir() / f"{name}.md"


def save(name: str, template: str, description: str = "") -> Path:
    if not NAME_RE.match(name):
        raise PromptError("Use lowercase letters, numbers and dashes for the name (max 32).")
    if not template.strip():
        raise PromptError("The prompt is empty.")
    header = f"---\ndescription: {description.strip() or 'Your prompt'}\n---\n\n"
    path = path_for(name)
    atomic_write(path, (header + template.strip() + "\n").encode("utf-8"))
    return path


def remove(name: str) -> bool:
    path = path_for(name)
    if path.exists():
        path.unlink()
        return True
    return False


def template_file(prompt: Prompt) -> str:
    return f"---\ndescription: {prompt.description}\n---\n\n{prompt.template}\n"


def git_diff(cwd: Path | None = None) -> str:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            raise PromptError("This folder is not a git repository.",
                              hint="Run it inside your project folder.")
        return result.stdout

    try:
        diff = run("diff", "--staged")
        if not diff.strip():
            diff = run("diff")
    except FileNotFoundError as exc:
        raise PromptError("git is not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise PromptError("git took too long to respond.") from exc
    if not diff.strip():
        raise PromptError("There are no changes to describe.",
                          hint="Edit some files (and `git add` them) first.")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n… (diff truncated)"
    return f"```diff\n{diff.rstrip()}\n```"


def render(prompt: Prompt, user_input: str = "", cwd: Path | None = None) -> str:
    """Fill a template. Plain replace (not str.format) so code with braces is safe."""
    text = prompt.template
    user_input = user_input.strip()
    if "{input}" in text:
        text = text.replace("{input}", user_input)
    elif user_input:
        text = f"{text}\n\n{user_input}"
    if prompt.needs_git:
        text = text.replace("{git_diff}", git_diff(cwd))
    if not user_input and "{input}" in prompt.template and not prompt.needs_git:
        raise PromptError(f"@{prompt.name} needs something to work on.",
                          hint=f'Example: kunji @{prompt.name} "your text"   or pipe text in')
    return re.sub(r"\n{3,}", "\n\n", text).strip()
