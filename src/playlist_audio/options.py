"""Translate application settings into yt-dlp API options."""

from pathlib import Path
from typing import Any

from playlist_audio.models import DownloadRequest
from playlist_audio.runtime import js_runtime_options

OUTPUT_TEMPLATE = "%(playlist_title|Playlist)s/%(playlist_index)03d - %(title)s [%(id)s].%(ext)s"


def build_ydl_options(request: DownloadRequest) -> dict[str, Any]:
    """Build a conservative, playlist-oriented yt-dlp configuration."""
    output_dir = request.output_dir.resolve()
    archive_file = request.archive_file.resolve()
    postprocessors: list[dict[str, Any]] = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": request.audio_quality,
        }
    ]

    if request.embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if request.embed_thumbnail:
        postprocessors.extend(
            [
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "EmbedThumbnail"},
            ]
        )

    options: dict[str, Any] = {
        "format": "bestaudio/best",
        "paths": {"home": str(output_dir)},
        "outtmpl": {"default": OUTPUT_TEMPLATE},
        "download_archive": str(archive_file),
        "continuedl": True,
        "ignoreerrors": True,
        "retries": 10,
        "fragment_retries": 10,
        "sleep_interval": 1,
        "max_sleep_interval": 3,
        "windowsfilenames": True,
        "writethumbnail": request.embed_thumbnail,
        "postprocessors": postprocessors,
        "js_runtimes": js_runtime_options(),
        "simulate": request.dry_run,
        "noplaylist": False,
    }

    if request.browser:
        options["cookiesfrombrowser"] = (
            request.browser.value,
            request.browser_profile,
            None,
            None,
        )
    if request.playlist_items:
        options["playlist_items"] = request.playlist_items

    return options


def default_archive_path(output_dir: Path) -> Path:
    """Keep non-secret download state beside the user's output library."""
    return output_dir / ".playlist-audio-archive.txt"
