from pathlib import Path

import pytest

from playlist_audio.web.request_parser import RequestError, parse_download_request

VALID_PAYLOAD = {
    "url": "https://www.youtube.com/playlist?list=PL123",
    "output": "downloads",
    "confirm_rights": True,
}


def test_parses_private_preview_request() -> None:
    request = parse_download_request(
        {
            **VALID_PAYLOAD,
            "browser": "firefox",
            "browser_profile": "default-release",
            "dry_run": True,
            "audio_quality": "0",
        }
    )

    assert request.browser is not None
    assert request.browser.value == "firefox"
    assert request.dry_run is True
    assert request.output_dir == Path("downloads")


def test_requires_rights_confirmation() -> None:
    with pytest.raises(RequestError, match="must confirm"):
        parse_download_request({**VALID_PAYLOAD, "confirm_rights": False})


@pytest.mark.parametrize("playlist_items", ["all", "1;rm", "1 2"])
def test_rejects_invalid_playlist_ranges(playlist_items: str) -> None:
    with pytest.raises(RequestError, match="Playlist selection"):
        parse_download_request({**VALID_PAYLOAD, "playlist_items": playlist_items})


def test_rejects_unknown_browser() -> None:
    with pytest.raises(RequestError):
        parse_download_request({**VALID_PAYLOAD, "browser": "unknown"})


def test_rejects_browser_profile_without_browser() -> None:
    with pytest.raises(RequestError, match="Select --browser"):
        parse_download_request({**VALID_PAYLOAD, "browser_profile": "Default"})


@pytest.mark.parametrize("field", ["dry_run", "embed_thumbnail", "embed_metadata"])
def test_rejects_non_boolean_flags(field: str) -> None:
    with pytest.raises(RequestError, match="must be true or false"):
        parse_download_request({**VALID_PAYLOAD, field: "yes"})


def test_audio_format_defaults_to_mp3() -> None:
    request = parse_download_request(VALID_PAYLOAD)

    assert request.audio_format == "mp3"


def test_audio_format_pass_through_when_valid() -> None:
    request = parse_download_request({**VALID_PAYLOAD, "audio_format": "opus"})

    assert request.audio_format == "opus"


def test_rejects_unsupported_audio_format() -> None:
    with pytest.raises(RequestError, match="Audio format"):
        parse_download_request({**VALID_PAYLOAD, "audio_format": "flac"})
