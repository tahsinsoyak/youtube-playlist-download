from pathlib import Path
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch

from playlist_audio.downloader import DownloadFailed, DownloadOutcome
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

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        if progress_hook:
            progress_hook(
                {
                    "status": "downloading",
                    "downloaded_bytes": 50,
                    "total_bytes": 100,
                    "speed": 2_048,
                    "eta": 4,
                    "info_dict": {
                        "title": "Test song",
                        "playlist_title": "Test playlist",
                        "playlist_index": 2,
                        "playlist_count": 4,
                    },
                }
            )
        finished.set()
        return DownloadOutcome(total_items=4, available_items=3, unavailable_items=1)

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        created = manager.create(make_request(tmp_path))
        assert finished.wait(timeout=2)

    result = manager.get(created["id"])
    assert result is not None
    assert result["state"] == "completed"
    assert result["progress"] == 100
    assert result["playlist_title"] == "Test playlist"
    assert result["downloaded_bytes"] == 50
    assert result["available_items"] == 3
    assert result["unavailable_items"] == 1
    assert "1 unavailable item(s) skipped" in result["message"]
    assert "url" not in result


def test_job_failure_surfaces_error_message(tmp_path: Path) -> None:
    finished = Event()

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        finished.set()
        raise DownloadFailed("Could not read the Chrome session.")

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        created = manager.create(make_request(tmp_path))
        assert finished.wait(timeout=2)
        deadline = monotonic() + 2
        while manager.get(created["id"])["state"] == "running" and monotonic() < deadline:
            sleep(0.01)

    result = manager.get(created["id"])
    assert result is not None
    assert result["state"] == "failed"
    assert result["message"] == "Could not read the Chrome session."
    assert result["progress"] is None


def test_unexpected_job_error_does_not_leak_internal_details(tmp_path: Path) -> None:
    finished = Event()

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        finished.set()
        raise RuntimeError("stack trace with a local file path")

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        created = manager.create(make_request(tmp_path))
        assert finished.wait(timeout=2)
        deadline = monotonic() + 2
        while manager.get(created["id"])["state"] == "running" and monotonic() < deadline:
            sleep(0.01)

    result = manager.get(created["id"])
    assert result is not None
    assert result["state"] == "failed"
    assert "stack trace" not in result["message"]
    assert result["message"] == "An unexpected local error occurred. Check the terminal output."


def test_jobs_added_during_download_run_in_fifo_order(tmp_path: Path) -> None:
    first_started = Event()
    release_first = Event()
    second_finished = Event()
    call_order: list[str] = []

    def fake_download(request, progress_hook=None) -> None:
        call_order.append(request.url)
        if len(call_order) == 1:
            first_started.set()
            assert release_first.wait(timeout=2)
        else:
            second_finished.set()

    first_request = make_request(tmp_path)
    second_request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL456",
        output_dir=tmp_path,
        archive_file=tmp_path / "archive.txt",
        dry_run=False,
    )
    manager = JobManager()

    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        first = manager.create(first_request)
        assert first_started.wait(timeout=2)
        second = manager.create(second_request)

        snapshot = manager.snapshot()
        assert snapshot["active"]["id"] == first["id"]
        assert snapshot["queued"][0]["id"] == second["id"]
        assert snapshot["queued"][0]["queue_position"] == 1

        release_first.set()
        assert second_finished.wait(timeout=2)
        deadline = monotonic() + 2
        while manager.get(second["id"])["state"] != "completed" and monotonic() < deadline:
            sleep(0.01)

    assert call_order == [first_request.url, second_request.url]
    assert manager.get(first["id"])["state"] == "completed"
    assert manager.get(second["id"])["state"] == "completed"
    assert manager.snapshot()["counts"] == {"running": 0, "queued": 0}
