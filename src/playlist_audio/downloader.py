"""Small yt-dlp adapter so the CLI remains easy to test."""

from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from playlist_audio.models import DownloadRequest
from playlist_audio.options import build_ydl_options


class DownloadFailed(RuntimeError):
    """User-facing download failure."""


def download(request: DownloadRequest) -> None:
    """Create output directories and execute one yt-dlp run."""
    request.output_dir.mkdir(parents=True, exist_ok=True)
    request.archive_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with YoutubeDL(build_ydl_options(request)) as ydl:
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
