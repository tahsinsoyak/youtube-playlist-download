from pathlib import Path
from threading import Event
from unittest.mock import patch

from playlist_audio.models import DownloadRequest
from playlist_audio.web.jobs import JobManager


def make_request(tmp_path: Path) -> DownloadRequest:
    return DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        dry_run=True,
    )


def test_job_completes_without_exposing_source_url(tmp_path: Path) -> None:
    finished = Event()

    def fake_download(request, progress_hook=None) -> None:
        if progress_hook:
            progress_hook(
                {
                    "status": "downloading",
                    "downloaded_bytes": 50,
                    "total_bytes": 100,
                    "info_dict": {"title": "Test song"},
                }
            )
        finished.set()

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        created = manager.create(make_request(tmp_path))
        assert finished.wait(timeout=2)

    result = manager.get(created["id"])
    assert result is not None
    assert result["state"] == "completed"
    assert result["progress"] == 100
    assert "url" not in result
