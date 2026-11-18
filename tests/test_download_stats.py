import importlib.util
import json
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parent.parent / "scripts" / "download_stats.py"
_spec = importlib.util.spec_from_file_location("download_stats", _path)
stats = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stats)


@pytest.mark.parametrize(
    ("n", "text"),
    [(0, "0"), (999, "999"), (1000, "1k"), (1234, "1.2k"), (25_400, "25.4k"), (1_234_567, "1.2M")],
)
def test_short_numbers(n, text):
    assert stats.short(n) == text


def test_merge_keeps_old_days_and_updates_recent_ones():
    history = {"2026-01-01": 5, "2026-11-17": 3}
    latest = {"2026-11-17": 7, "2026-11-18": 2}  # 01-01 is older than 180 days now
    assert stats.merge(history, latest) == {"2026-01-01": 5, "2026-11-17": 7, "2026-11-18": 2}


def test_run_writes_history_and_badge(tmp_path):
    history, badge = tmp_path / "history.json", tmp_path / "downloads.json"
    history.write_text(json.dumps({"daily": {"2026-01-01": 1000}}))

    total = stats.run(history, badge, lambda: {"2026-11-18": 234})

    assert total == 1234
    saved = json.loads(history.read_text())
    assert saved["daily"] == {"2026-01-01": 1000, "2026-11-18": 234} and saved["total"] == 1234
    assert json.loads(badge.read_text()) == {
        "schemaVersion": 1,
        "label": "downloads",
        "message": "1.2k",
        "color": "2563eb",
        "labelColor": "1f2328",
    }


def test_first_run_without_history(tmp_path):
    history, badge = tmp_path / "history.json", tmp_path / "downloads.json"
    assert stats.run(history, badge, lambda: {"2026-11-18": 12}) == 12
    assert json.loads(badge.read_text())["message"] == "12"


def test_fetch_keeps_only_downloads_without_mirrors(monkeypatch):
    answer = {
        "data": [
            {"category": "with_mirrors", "date": "2026-11-18", "downloads": 50},
            {"category": "without_mirrors", "date": "2026-11-18", "downloads": 40},
        ],
        "package": "kunji",
        "type": "overall_downloads",
    }

    class FakePypistats:
        @staticmethod
        def overall(package, **kwargs):
            assert kwargs == {"mirrors": False, "total": "daily", "format": "json"}
            return json.dumps(answer)

    monkeypatch.setitem(__import__("sys").modules, "pypistats", FakePypistats)
    assert stats.fetch_daily() == {"2026-11-18": 40}


def test_fetch_fails_clearly_on_no_data(monkeypatch):
    class FakePypistats:
        @staticmethod
        def overall(package, **kwargs):
            return "No data found for https://pypi.org/project/kunji/"

    monkeypatch.setitem(__import__("sys").modules, "pypistats", FakePypistats)
    with pytest.raises(RuntimeError, match="pypistats.org"):
        stats.fetch_daily()
