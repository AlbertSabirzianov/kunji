import json
import subprocess
import sys
import time

from typer.testing import CliRunner

from kunji import checkin, upgrade
from kunji.cli import app
from kunji.config import Config, cache_dir

runner = CliRunner()


def _cache_latest(version: str) -> None:
    path = cache_dir() / "update.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched_at": time.time(), "latest": version}))


def test_notice_only_when_newer():
    cfg = Config.load()
    assert upgrade.notice(cfg) is None
    _cache_latest("99.0.0")
    line = upgrade.notice(cfg)
    assert line is not None and "99.0.0" in line.plain and "kunji upgrade" in line.plain
    cfg.set("updates.check", False)
    assert upgrade.notice(cfg) is None


def test_upgrade_says_up_to_date(monkeypatch):
    monkeypatch.setattr(checkin, "check_updates", lambda cfg, force=False: None)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0 and "latest version" in result.output


def test_upgrade_check_only(monkeypatch):
    monkeypatch.setattr(checkin, "check_updates", lambda cfg, force=False: "99.0.0")
    result = runner.invoke(app, ["upgrade", "--check"])
    assert result.exit_code == 0 and "kunji upgrade" in result.output


def test_upgrade_runs_pip_with_same_python(monkeypatch):
    calls = {}
    monkeypatch.setattr(checkin, "check_updates", lambda cfg, force=False: "99.0.0")
    monkeypatch.setattr(upgrade, "on_windows", lambda: False)
    monkeypatch.setattr(subprocess, "call", lambda cmd: calls.setdefault("cmd", cmd) and 0)
    result = runner.invoke(app, ["upgrade"])
    assert calls["cmd"][:3] == [sys.executable, "-m", "pip"]
    assert "--upgrade" in calls["cmd"] and "kunji" in calls["cmd"]
    assert result.exit_code == 0


def test_windows_upgrade_script_is_valid_python(monkeypatch):
    launched = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            launched["args"] = args

    monkeypatch.setattr(upgrade, "on_windows", lambda: True)
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    from io import StringIO

    from rich.console import Console

    assert upgrade.start_upgrade(Console(file=StringIO())) == 0
    script = launched["args"][2]
    compile(script, "<upgrade>", "exec")  # must not be a syntax error
    assert "pip" in script and "--upgrade" in script


def test_standalone_points_to_download(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    from io import StringIO

    from rich.console import Console

    out = StringIO()
    assert upgrade.start_upgrade(Console(file=out, width=200)) == 0
    assert "kunji-windows-x64.exe" in out.getvalue()
