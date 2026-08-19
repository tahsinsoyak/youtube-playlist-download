"""User-level default settings loaded from a local TOML config file."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".playlist-audio" / "config.toml"

_STRING_FIELDS = ("output", "browser", "browser_profile", "audio_quality")


@dataclass(frozen=True, slots=True)
class ConfigDefaults:
    """Optional overrides for command defaults; unset fields keep the built-in default."""

    output: str | None = None
    browser: str | None = None
    browser_profile: str | None = None
    audio_quality: str | None = None
    port: int | None = None


def load_config(path: Path | None = None) -> ConfigDefaults:
    """Read known keys from a TOML file; ignore unknown keys and missing or broken files."""
    config_path = path or DEFAULT_CONFIG_PATH
    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError, OSError):
        return ConfigDefaults()

    values: dict[str, object] = {
        key: data[key] for key in _STRING_FIELDS if isinstance(data.get(key), str)
    }
    port = data.get("port")
    if isinstance(port, int) and not isinstance(port, bool):
        values["port"] = port
    return ConfigDefaults(**values)
