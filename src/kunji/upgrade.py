"""Update notice and `kunji upgrade`.

The notice uses the result of the daily background version check (cached), so showing it
never slows startup. Turn it off with: kunji config set updates.check false
"""

from __future__ import annotations

import os
import subprocess
import sys

from rich.text import Text

from kunji import __version__, checkin
from kunji.config import Config

RELEASES_URL = "https://github.com/testwithsuraj/kunji/releases/latest"
EXE_URL = "https://github.com/testwithsuraj/kunji/releases/latest/download/kunji-windows-x64.exe"


def is_standalone() -> bool:
    """True when running as the PyInstaller .exe / binary (not installed with pip)."""
    return bool(getattr(sys, "frozen", False))


def available(cfg: Config) -> str | None:
    if not cfg.get("updates.check", True):
        return None
    return checkin.cached_update_notice()


def notice(cfg: Config) -> Text | None:
    latest = available(cfg)
    if not latest:
        return None
    how = "download the new version" if is_standalone() else "kunji upgrade"
    return Text.assemble(
        ("⬆ ", "k.accent"),
        (f"kunji {latest} is available", "k.accent"),
        (f" (you have {__version__}). ", "k.dim"),
        ("Upgrade: ", "k.dim"),
        (how, "k.accent"),
    )


def on_windows() -> bool:
    return os.name == "nt"


def pip_command() -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--upgrade", "kunji"]


def start_upgrade(console) -> int:
    """Upgrade with the same Python that runs kunji. Returns an exit code."""
    if is_standalone():
        console.print(Text.assemble(("You're using the standalone kunji.exe. ", "k.dim"),
                                    "Download the new version: ", (EXE_URL, "k.accent")))
        return 0
    cmd = pip_command()
    if on_windows():
        # Windows locks the running kunji.exe launcher, so pip can't replace it while kunji is
        # open. Run pip in a new window that starts after this process exits.
        script = (
            "import subprocess, sys, time; time.sleep(1.5); "
            f"code = subprocess.call({cmd!r}); "
            "print(); "
            "print('Done! Run kunji again.' if code == 0 else 'Upgrade failed, see above.'); "
            "input('Press Enter to close this window...')"
        )
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen([sys.executable, "-c", script], creationflags=flags,
                         close_fds=True)
        console.print(Text.assemble(("✓ ", "k.ok"), "Upgrading in a new window. ",
                                    ("kunji will close now; open it again when it says Done.",
                                     "k.dim")))
        return 0
    console.print(Text(" ".join(["$", "python", "-m", "pip", "install", "--upgrade", "kunji"]),
                       style="k.dim"))
    code = subprocess.call(cmd)
    if code == 0:
        console.print(Text.assemble(("✓ ", "k.ok"), "Upgraded. Run kunji again to use the new "
                                                     "version."))
    else:
        console.print(Text.assemble(("✗ ", "k.err"), "Upgrade failed. Try it yourself: ",
                                    ("python -m pip install --upgrade kunji", "k.accent")))
    return code
