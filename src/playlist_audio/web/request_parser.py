"""Validate browser-submitted job settings without trusting the UI."""

import re
from pathlib import Path
from typing import Any

from playlist_audio.models import Browser, DownloadRequest
from playlist_audio.options import default_archive_path
from playlist_audio.validation import (
    ValidationError,
    validate_audio_quality,
    validate_browser_profile,
    validate_youtube_url,
)

PLAYLIST_ITEMS_PATTERN = re.compile(r"^[0-9,:-]+$")


class RequestError(ValueError):
    """Raised when a web request cannot become a safe download request."""


def _optional_text(payload: dict[str, Any], key: str, max_length: int) -> str | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    if not isinstance(value, str) or len(value) > max_length:
        raise RequestError(f"Invalid {key} field.")
    return value.strip() or None


def _boolean(payload: dict[str, Any], key: str, default: bool) -> bool:
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise RequestError(f"{key} must be true or false.")
    return value


def parse_download_request(payload: dict[str, Any]) -> DownloadRequest:
    """Convert a bounded JSON object into the shared immutable model."""
    if payload.get("confirm_rights") is not True:
        raise RequestError("You must confirm that you are authorized to download this content.")

    url = _optional_text(payload, "url", 2_048)
    output = _optional_text(payload, "output", 500) or "downloads"
    browser_value = _optional_text(payload, "browser", 32)
    browser_profile = _optional_text(payload, "browser_profile", 300)
    playlist_items = _optional_text(payload, "playlist_items", 64)

    try:
        browser = Browser(browser_value) if browser_value else None
        validated_url = validate_youtube_url(url or "")
        audio_quality = validate_audio_quality(str(payload.get("audio_quality", "0")))
        validate_browser_profile(browser, browser_profile)
    except (ValueError, ValidationError) as error:
        raise RequestError(str(error)) from error

    if playlist_items and not PLAYLIST_ITEMS_PATTERN.fullmatch(playlist_items):
        raise RequestError(
            "Playlist selection may contain only numbers, commas, hyphens, and colons."
        )
    if "\x00" in output:
        raise RequestError("Invalid output folder.")

    output_dir = Path(output).expanduser()
    return DownloadRequest(
        url=validated_url,
        output_dir=output_dir,
        archive_file=default_archive_path(output_dir),
        browser=browser,
        browser_profile=browser_profile,
        audio_quality=audio_quality,
        playlist_items=playlist_items,
        dry_run=_boolean(payload, "dry_run", True),
        embed_thumbnail=_boolean(payload, "embed_thumbnail", True),
        embed_metadata=_boolean(payload, "embed_metadata", True),
    )
