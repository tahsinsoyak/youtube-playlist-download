import pytest

from playlist_audio.models import Browser
from playlist_audio.validation import (
    ValidationError,
    validate_audio_format,
    validate_audio_quality,
    validate_browser_profile,
    validate_youtube_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/playlist?list=PL123",
        "https://music.youtube.com/playlist?list=PL123",
        "https://youtu.be/abc123",
        "https://WWW.YOUTUBE.COM/watch?v=abc123",
    ],
)
def test_accepts_supported_youtube_urls(url: str) -> None:
    assert validate_youtube_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://youtube.com/watch?v=abc",
        "https://example.com/watch?v=abc",
        "file:///tmp/video",
        "https://youtube.com/",
    ],
)
def test_rejects_unsafe_or_incomplete_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        validate_youtube_url(url)


def test_audio_quality_range() -> None:
    assert validate_audio_quality("0") == "0"
    assert validate_audio_quality("10") == "10"

    with pytest.raises(ValidationError):
        validate_audio_quality("11")
    with pytest.raises(ValidationError):
        validate_audio_quality("-1")


@pytest.mark.parametrize("value", ["mp3", "m4a", "opus", "M4A", " opus "])
def test_accepts_supported_audio_formats(value: str) -> None:
    assert validate_audio_format(value) == value.strip().lower()


def test_rejects_unsupported_audio_format() -> None:
    with pytest.raises(ValidationError, match="m4a, mp3, opus"):
        validate_audio_format("flac")


def test_profile_requires_browser() -> None:
    with pytest.raises(ValidationError):
        validate_browser_profile(None, "Default")

    validate_browser_profile(Browser.CHROME, "Default")
