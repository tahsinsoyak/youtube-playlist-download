"""Small yt-dlp adapter so the CLI remains easy to test."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from playlist_audio.models import DownloadRequest
from playlist_audio.options import build_ydl_options


class DownloadFailed(RuntimeError):
    """User-facing download failure."""


def download(
    request: DownloadRequest,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Create output directories and execute one yt-dlp run."""
    request.output_dir.mkdir(parents=True, exist_ok=True)
    request.archive_file.parent.mkdir(parents=True, exist_ok=True)
    options = build_ydl_options(request)
    if progress_hook:
        options["progress_hooks"] = [progress_hook]

    try:
        with YoutubeDL(options) as ydl:
            return_code = ydl.download([request.url])
    except DownloadError as error:
        raise DownloadFailed(str(error)) from error

    if return_code:
        raise DownloadFailed(
            "Bazı öğeler indirilemedi. Ayrıntılar için yukarıdaki yt-dlp çıktısını inceleyin."
        )


def output_location(request: DownloadRequest) -> Path:
    """Expose the resolved destination for a final CLI message."""
    return request.output_dir.resolve()
