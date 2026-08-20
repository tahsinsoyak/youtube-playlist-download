"""Input validation kept separate from network and filesystem operations."""

from urllib.parse import urlparse

from playlist_audio.models import Browser

YOUTUBE_HOSTS = {
    "youtu.be",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}

AUDIO_FORMATS = {"mp3", "m4a", "opus"}


class ValidationError(ValueError):
    """Raised when a CLI input is unsafe or unsupported."""


def validate_youtube_url(value: str) -> str:
    """Accept only HTTPS YouTube URLs supported by this focused tool."""
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()

    if parsed.scheme != "https" or host not in YOUTUBE_HOSTS:
        raise ValidationError("Only https://youtube.com and https://youtu.be URLs are accepted.")
    if not parsed.path or parsed.path == "/":
        raise ValidationError("Enter the complete video or playlist URL.")
    return value.strip()


def validate_audio_quality(value: str) -> str:
    """Validate FFmpeg VBR quality where 0 is best and 10 is worst."""
    try:
        quality = int(value)
    except ValueError as error:
        raise ValidationError("Audio quality must be an integer from 0 to 10.") from error

    if quality not in range(11):
        raise ValidationError("Audio quality must be from 0 to 10; 0 is best.")
    return str(quality)


def validate_audio_format(value: str) -> str:
    """Accept only the FFmpeg audio codecs this tool tests and documents."""
    normalized = value.strip().lower()
    if normalized not in AUDIO_FORMATS:
        allowed = ", ".join(sorted(AUDIO_FORMATS))
        raise ValidationError(f"Audio format must be one of: {allowed}.")
    return normalized


def validate_browser_profile(browser: Browser | None, profile: str | None) -> None:
    """A browser profile has no meaning without a selected browser."""
    if profile and browser is None:
        raise ValidationError("Select --browser before using --browser-profile.")
