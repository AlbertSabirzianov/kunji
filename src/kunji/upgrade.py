"""Update notice and `kunji upgrade`.

The notice uses the result of the daily background version check (cached), so showing it
never slows startup. Turn it off with: kunji config set updates.check false
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from rich.text import Text

from kunji import __version__, checkin
from kunji.config import Config

RELEASES_URL = "https://github.com/testwithsuraj/kunji/releases/latest"
EXE_URL = "https://github.com/testwithsuraj/kunji/releases/latest/download/kunji-windows-x64.exe"
INSTALL_SH = "https://kunji.iamsuraj.me/install.sh"
INSTALL_PS1 = "https://kunji.iamsuraj.me/install.ps1"


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


def installed_with_uv() -> bool:
    """True when kunji was installed with `uv tool install` (what install.sh / install.ps1 do).

    uv writes a receipt into the tool's environment. That environment has no pip, so the pip
    upgrade would fail there.
    """
    return (Path(sys.prefix) / "uv-receipt.toml").is_file()


def find_uv() -> str | None:
    found = shutil.which("uv")
    if found:
        return found
    name = "uv.exe" if on_windows() else "uv"
    dirs = [os.environ.get("XDG_BIN_HOME", ""), str(Path.home() / ".local" / "bin")]
    dirs.append(os.path.join(os.environ.get("CARGO_HOME", str(Path.home() / ".cargo")), "bin"))
    for folder in dirs:
        candidate = Path(folder) / name if folder else None
        if candidate and candidate.is_file():
            return str(candidate)
    return None


def installer_command() -> str:
    """The one-line installer for this OS (running it again also upgrades)."""
    if on_windows():
        return f"irm {INSTALL_PS1} | iex"
    return f"curl -fsSL {INSTALL_SH} | sh"


def pip_command() -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--upgrade", "kunji"]


def upgrade_command() -> list[str] | None:
    """The command that upgrades this install, or None if it can't be run from here."""
    if installed_with_uv():
        uv = find_uv()
        return [uv, "tool", "upgrade", "kunji"] if uv else None
    return pip_command()


def manual_command() -> str:
    if installed_with_uv():
        return "uv tool upgrade kunji"
    return "python -m pip install --upgrade kunji"


def start_upgrade(console) -> int:
    """Upgrade kunji the same way it was installed. Returns an exit code."""
    if is_standalone():
        console.print(
            Text.assemble(
                ("You're using the standalone kunji.exe. ", "k.dim"),
                "Download the new version: ",
                (EXE_URL, "k.accent"),
            )
        )
        return 0
    cmd = upgrade_command()
    if cmd is None:
        console.print(
            Text.assemble(
                ("✗ ", "k.err"),
                "Can't find uv, which installed kunji. Run the installer again to upgrade: ",
                (installer_command(), "k.accent"),
            )
        )
        return 1
    if on_windows():
        # Windows locks the running kunji.exe launcher, so pip/uv can't replace it while kunji
        # is open. Run the upgrade in a new window that starts after this process exits.
        script = (
            "import subprocess, sys, time; time.sleep(1.5); "
            f"code = subprocess.call({cmd!r}); "
            "print(); "
            "print('Done! Run kunji again.' if code == 0 else 'Upgrade failed, see above.'); "
            "input('Press Enter to close this window...')"
        )
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen([sys.executable, "-c", script], creationflags=flags, close_fds=True)
        console.print(
            Text.assemble(
                ("✓ ", "k.ok"),
                "Upgrading in a new window. ",
                ("kunji will close now; open it again when it says Done.", "k.dim"),
            )
        )
        return 0
    console.print(Text("Running: " + manual_command(), style="k.dim"))
    code = subprocess.call(cmd)
    if code == 0:
        console.print(
            Text.assemble(("✓ ", "k.ok"), "Upgraded. Run kunji again to use the new version.")
        )
    else:
        console.print(
            Text.assemble(
                ("✗ ", "k.err"),
                "Upgrade failed. Try it yourself: ",
                (manual_command(), "k.accent"),
            )
        )
    return code
