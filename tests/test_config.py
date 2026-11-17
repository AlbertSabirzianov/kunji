import pytest

from kunji.config import Config, ConfigError, config_path


def test_invalid_toml_produces_config_error(tmp_path, isolated):
    """Malformed TOML in the config file should raise ConfigError with a clear message."""
    # The 'isolated' fixture (autouse in conftest) sets KUNJI_HOME to tmp_path / "home"
    # so config_path() resolves to tmp_path / "home" / "config" / "config.toml"

    cfg_dir = tmp_path / "home" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    malformed = cfg_dir / "config.toml"
    malformed.write_text("this is not valid toml [[[\n", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        Config.load()

    err_msg = str(exc_info.value)
    assert "not valid TOML" in err_msg
    assert "config.toml" in err_msg
