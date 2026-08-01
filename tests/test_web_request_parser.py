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
