import json
import subprocess
import sys
import time

import pytest
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


def _fake_uv_install(monkeypatch, tmp_path, uv: str | None):
    (tmp_path / "uv-receipt.toml").write_text("[tool]\n")
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(upgrade, "find_uv", lambda: uv)
    monkeypatch.setattr(upgrade, "on_windows", lambda: False)
    monkeypatch.setattr(checkin, "check_updates", lambda cfg, force=False: "99.0.0")


def test_pip_install_is_not_a_uv_install():
    assert not upgrade.installed_with_uv()
    assert upgrade.upgrade_command() == upgrade.pip_command()


def test_uv_install_upgrades_with_uv(monkeypatch, tmp_path):
    calls = {}
    _fake_uv_install(monkeypatch, tmp_path, "/fake/bin/uv")
    monkeypatch.setattr(subprocess, "call", lambda cmd: calls.setdefault("cmd", cmd) and 0)
    result = runner.invoke(app, ["upgrade"])
    assert calls["cmd"] == ["/fake/bin/uv", "tool", "upgrade", "kunji"]
    assert result.exit_code == 0 and "uv tool upgrade kunji" in result.output


def test_uv_install_without_uv_points_to_installer(monkeypatch, tmp_path):
    _fake_uv_install(monkeypatch, tmp_path, None)
    monkeypatch.setattr(subprocess, "call", lambda cmd: pytest.fail("must not run anything"))
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 1 and "install.sh" in result.output


def test_windows_uv_upgrade_runs_in_new_window(monkeypatch, tmp_path):
    launched = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            launched["args"] = args

    _fake_uv_install(monkeypatch, tmp_path, r"C:\Users\me\.local\bin\uv.exe")
    monkeypatch.setattr(upgrade, "on_windows", lambda: True)
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    from io import StringIO

    from rich.console import Console

    assert upgrade.start_upgrade(Console(file=StringIO())) == 0
    script = launched["args"][2]
    compile(script, "<upgrade>", "exec")
    assert "uv.exe" in script and "'tool', 'upgrade', 'kunji'" in script
    assert "install.ps1" in upgrade.installer_command()
