"""Application data models."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Browser(StrEnum):
    """Browsers supported by yt-dlp cookie extraction."""

    BRAVE = "brave"
    CHROME = "chrome"
    CHROMIUM = "chromium"
    EDGE = "edge"
    FIREFOX = "firefox"
    OPERA = "opera"
    VIVALDI = "vivaldi"


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    """Validated settings for one download invocation."""

    url: str
    output_dir: Path
    archive_file: Path
    browser: Browser | None = None
    browser_profile: str | None = None
    audio_quality: str = "0"
    playlist_items: str | None = None
    dry_run: bool = False
    embed_thumbnail: bool = True
    embed_metadata: bool = True
