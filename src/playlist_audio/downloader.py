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


class DownloadFailed(RuntimeError):
    """User-facing download failure."""


@dataclass(frozen=True, slots=True)
class DownloadOutcome:
    """Summarize accessible and skipped items without exposing their URLs."""

    total_items: int
    available_items: int
    unavailable_items: int


def _summarize_info(info: dict[str, Any] | None) -> DownloadOutcome:
    if not info:
        raise DownloadFailed("Erişilebilir bir video veya playlist öğesi bulunamadı.")

    entries = info.get("entries")
    if entries is None:
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    resolved_entries = list(entries)
    available = sum(item is not None for item in resolved_entries)
    unavailable = len(resolved_entries) - available
    if available == 0:
        raise DownloadFailed("Playlist içinde erişilebilir bir öğe bulunamadı.")
    return DownloadOutcome(
        total_items=len(resolved_entries),
        available_items=available,
        unavailable_items=unavailable,
    )


def _browser_session_error(request: DownloadRequest) -> str:
    browser = request.browser.value.capitalize() if request.browser else "Tarayıcı"
    if request.browser and request.browser.value in {
        "brave",
        "chrome",
        "chromium",
        "edge",
        "opera",
        "vivaldi",
    }:
        return (
            f"{browser} oturumu okunamadı. Windows, tarayıcı açıkken cookie "
            "veritabanını kilitliyor. Arayüzü başka bir tarayıcıda açın; "
            f"{browser} pencerelerini ve arka plan süreçlerini tamamen kapatıp yeniden deneyin. "
            "Alternatif olarak YouTube'a Firefox'ta giriş yapıp Firefox'u seçin."
        )
    return (
        f"{browser} oturumu okunamadı. Doğru profile giriş yaptığınızı kontrol edin, "
        "tarayıcıyı tamamen kapatıp yeniden deneyin."
    )


def download(
    request: DownloadRequest,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
) -> DownloadOutcome:
    """Create output directories and execute one yt-dlp run."""
    request.output_dir.mkdir(parents=True, exist_ok=True)
    request.archive_file.parent.mkdir(parents=True, exist_ok=True)
    options = build_ydl_options(request)
    if progress_hook:
        options["progress_hooks"] = [progress_hook]

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
