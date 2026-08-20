from pathlib import Path

from playlist_audio.config import ConfigDefaults, load_config


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    assert load_config(tmp_path / "missing.toml") == ConfigDefaults()


def test_reads_known_string_and_int_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'output = "D:/Music"\n'
        'browser = "firefox"\n'
        'browser_profile = "default-release"\n'
        'audio_quality = "2"\n'
        'audio_format = "opus"\n'
        "port = 9000\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output == "D:/Music"
    assert config.browser == "firefox"
    assert config.browser_profile == "default-release"
    assert config.audio_quality == "2"
    assert config.audio_format == "opus"
    assert config.port == 9000


def test_ignores_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text('output = "downloads"\nsome_future_key = "value"\n', encoding="utf-8")

    config = load_config(config_path)

    assert config.output == "downloads"


def test_ignores_wrong_typed_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text('port = "not-a-number"\noutput = 42\n', encoding="utf-8")

    config = load_config(config_path)

    assert config.port is None
    assert config.output is None


def test_malformed_toml_returns_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("this is not [valid toml", encoding="utf-8")

    assert load_config(config_path) == ConfigDefaults()
