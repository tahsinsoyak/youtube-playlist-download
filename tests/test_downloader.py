from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.cookies import CookieLoadError

from playlist_audio.downloader import DownloadFailed, download
from playlist_audio.models import Browser, DownloadRequest


def test_download_creates_state_directories_and_calls_yt_dlp(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path / "nested" / "music",
        archive_file=tmp_path / "state" / "archive.txt",
        dry_run=True,
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.download.return_value = 0

    with patch("playlist_audio.downloader.YoutubeDL", return_value=ydl):
        download(request)

    assert request.output_dir.is_dir()
    assert request.archive_file.parent.is_dir()
    ydl.download.assert_called_once_with([request.url])


def test_download_attaches_progress_hook(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/watch?v=abc123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
    )
    hook = MagicMock()
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.download.return_value = 0

    with patch("playlist_audio.downloader.YoutubeDL", return_value=ydl) as youtube_dl:
        download(request, progress_hook=hook)

    assert youtube_dl.call_args.args[0]["progress_hooks"] == [hook]


def test_chrome_cookie_lock_has_actionable_error(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        browser=Browser.CHROME,
        dry_run=True,
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.download.side_effect = CookieLoadError("failed to load cookies")

    with (
        patch("playlist_audio.downloader.YoutubeDL", return_value=ydl),
        pytest.raises(DownloadFailed, match="cookie veritabanını kilitliyor"),
    ):
        download(request)
