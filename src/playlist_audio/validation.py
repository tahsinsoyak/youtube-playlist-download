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


class ValidationError(ValueError):
    """Raised when a CLI input is unsafe or unsupported."""


def validate_youtube_url(value: str) -> str:
    """Accept only HTTPS YouTube URLs supported by this focused tool."""
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()

    if parsed.scheme != "https" or host not in YOUTUBE_HOSTS:
        raise ValidationError(
            "Yalnızca https://youtube.com veya https://youtu.be adresleri kabul edilir."
        )
    if not parsed.path or parsed.path == "/":
        raise ValidationError("Video veya playlist adresinin tamamını girin.")
    return value.strip()


def validate_audio_quality(value: str) -> str:
    """Validate FFmpeg VBR quality where 0 is best and 10 is worst."""
    try:
        quality = int(value)
    except ValueError as error:
        raise ValidationError("Ses kalitesi 0 ile 10 arasında bir tam sayı olmalıdır.") from error

    if quality not in range(11):
        raise ValidationError("Ses kalitesi 0 ile 10 arasında olmalıdır; 0 en iyisidir.")
    return str(quality)


def validate_browser_profile(browser: Browser | None, profile: str | None) -> None:
    """A browser profile has no meaning without a selected browser."""
    if profile and browser is None:
        raise ValidationError("--browser-profile kullanmak için --browser da belirtin.")
