"""Small yt-dlp adapter so the CLI remains easy to test."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.cookies import CookieLoadError
from yt_dlp.utils import DownloadError

from playlist_audio.models import DownloadRequest
from playlist_audio.options import build_ydl_options
from playlist_audio.preflight import readiness_error


class DownloadFailed(RuntimeError):
    """User-facing download failure."""


class DownloadCancelled(RuntimeError):
    """A running download was cancelled by the local user."""


@dataclass(frozen=True, slots=True)
class DownloadOutcome:
    """Summarize accessible and skipped items without exposing their URLs."""

    total_items: int
    available_items: int
    unavailable_items: int


def _summarize_info(info: dict[str, Any] | None) -> DownloadOutcome:
    if not info:
        raise DownloadFailed("No accessible video or playlist item was found.")

    entries = info.get("entries")
    if entries is None:
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    resolved_entries = list(entries)
    available = sum(item is not None for item in resolved_entries)
    unavailable = len(resolved_entries) - available
    if available == 0:
        raise DownloadFailed("The playlist contains no accessible items.")
    return DownloadOutcome(
        total_items=len(resolved_entries),
        available_items=available,
        unavailable_items=unavailable,
    )


def _browser_session_error(request: DownloadRequest) -> str:
    browser = request.browser.value.capitalize() if request.browser else "Browser"
    if request.browser and request.browser.value in {
        "brave",
        "chrome",
        "chromium",
        "edge",
        "opera",
        "vivaldi",
    }:
        return (
            f"Could not read the {browser} session. Windows locks the cookie "
            "database while the browser is open. "
            f"Close every {browser} window and background process, then try again. "
            "Alternatively, sign in to YouTube with Firefox and select Firefox."
        )
    return (
        f"Could not read the {browser} session. Confirm you are signed in to the "
        "correct profile, close the browser completely, and try again."
    )


def download(
    request: DownloadRequest,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
) -> DownloadOutcome:
    """Create output directories and execute one yt-dlp run."""
    setup_error = readiness_error(dry_run=request.dry_run)
    if setup_error:
        raise DownloadFailed(setup_error)

    request.output_dir.mkdir(parents=True, exist_ok=True)
    request.archive_file.parent.mkdir(parents=True, exist_ok=True)
    options = build_ydl_options(request)
    if progress_hook:
        options["progress_hooks"] = [progress_hook]
        options["postprocessor_hooks"] = [progress_hook]

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(request.url, download=True)
    except (CookieLoadError, PermissionError) as error:
        raise DownloadFailed(_browser_session_error(request)) from error
    except DownloadError as error:
        raise DownloadFailed(str(error)) from error

    return _summarize_info(info)


def output_location(request: DownloadRequest) -> Path:
    """Expose the resolved destination for a final CLI message."""
    return request.output_dir.resolve()
