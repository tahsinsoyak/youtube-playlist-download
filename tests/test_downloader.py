from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.cookies import CookieLoadError
from yt_dlp.utils import DownloadError

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
    ydl.extract_info.return_value = {
        "_type": "playlist",
        "entries": [{"id": "one"}, {"id": "two"}],
    }

    with patch("playlist_audio.downloader.YoutubeDL", return_value=ydl):
        outcome = download(request)

    assert request.output_dir.is_dir()
    assert request.archive_file.parent.is_dir()
    ydl.extract_info.assert_called_once_with(request.url, download=True)
    assert outcome.available_items == 2
    assert outcome.unavailable_items == 0


def test_download_attaches_progress_hook(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/watch?v=abc123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
    )
    hook = MagicMock()
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.return_value = {"id": "abc123"}

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
    ydl.extract_info.side_effect = CookieLoadError("failed to load cookies")

    with (
        patch("playlist_audio.downloader.YoutubeDL", return_value=ydl),
        pytest.raises(DownloadFailed, match="locks the cookie database"),
    ):
        download(request)


def test_download_reports_unavailable_playlist_entries(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        dry_run=True,
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.return_value = {
        "_type": "playlist",
        "entries": [{"id": "one"}, None, {"id": "three"}],
    }

    with patch("playlist_audio.downloader.YoutubeDL", return_value=ydl):
        outcome = download(request)

    assert outcome.total_items == 3
    assert outcome.available_items == 2
    assert outcome.unavailable_items == 1


def test_yt_dlp_download_error_becomes_download_failed(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/watch?v=abc123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.side_effect = DownloadError("Video unavailable")

    with (
        patch("playlist_audio.downloader.YoutubeDL", return_value=ydl),
        pytest.raises(DownloadFailed, match="Video unavailable"),
    ):
        download(request)


def test_firefox_cookie_lock_uses_generic_error(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        browser=Browser.FIREFOX,
        dry_run=True,
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.side_effect = CookieLoadError("failed to load cookies")

    with (
        patch("playlist_audio.downloader.YoutubeDL", return_value=ydl),
        pytest.raises(DownloadFailed, match="signed in to the correct profile") as excinfo,
    ):
        download(request)
    assert "Windows locks the cookie database" not in str(excinfo.value)


def test_download_fails_when_no_playlist_entry_is_available(tmp_path: Path) -> None:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        dry_run=True,
    )
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.return_value = {"_type": "playlist", "entries": [None, None]}

    with (
        patch("playlist_audio.downloader.YoutubeDL", return_value=ydl),
        pytest.raises(DownloadFailed, match="no accessible items"),
    ):
        download(request)
