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


def test_cancel_removes_a_queued_job(tmp_path: Path) -> None:
    first_started = Event()
    release_first = Event()

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        first_started.set()
        assert release_first.wait(timeout=2)
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        active = manager.create(make_request(tmp_path))
        assert first_started.wait(timeout=2)
        queued = manager.create(make_request(tmp_path))

        cancelled = manager.cancel(queued["id"])
        assert cancelled is not None
        assert cancelled["state"] == "cancelled"

        snapshot = manager.snapshot()
        assert snapshot["queued"] == []
        assert manager.get(queued["id"])["state"] == "cancelled"

        release_first.set()
        deadline = monotonic() + 2
        while manager.get(active["id"])["state"] == "running" and monotonic() < deadline:
            sleep(0.01)


def test_can_cancel_the_active_job(tmp_path: Path) -> None:
    started = Event()
    release = Event()

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        started.set()
        assert release.wait(timeout=2)
        if progress_hook:
            progress_hook({"status": "downloading"})
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        active = manager.create(make_request(tmp_path))
        assert started.wait(timeout=2)

        cancelled = manager.cancel(active["id"])
        assert cancelled is not None
        assert manager.get(active["id"])["state"] == "running"
        assert manager.get(active["id"])["message"] == "Cancellation requested"

        release.set()
        deadline = monotonic() + 2
        while manager.get(active["id"])["state"] == "running" and monotonic() < deadline:
            sleep(0.01)

    assert manager.get(active["id"])["state"] == "cancelled"


def test_cancel_unknown_job_returns_none() -> None:
    manager = JobManager()
    assert manager.cancel("does-not-exist") is None


def test_can_retry_a_failed_job_during_the_same_session(tmp_path: Path) -> None:
    calls = 0

    def flaky_download(request, progress_hook=None) -> DownloadOutcome:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise DownloadFailed("Temporary failure")
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    manager = JobManager()
    with patch("playlist_audio.web.jobs.download", side_effect=flaky_download):
        failed = manager.create(make_request(tmp_path))
        deadline = monotonic() + 2
        while (
            manager.get(failed["id"])["state"] in {"queued", "running"} and monotonic() < deadline
        ):
            sleep(0.01)

        retried = manager.retry(failed["id"])
        assert retried is not None
        deadline = monotonic() + 2
        while (
            manager.get(retried["id"])["state"] in {"queued", "running"} and monotonic() < deadline
        ):
            sleep(0.01)

    assert manager.get(retried["id"])["state"] == "completed"


def test_history_is_trimmed_after_jobs_finish(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    manager = JobManager(state_path=state_path)

    with patch("playlist_audio.web.jobs.download", return_value=DownloadOutcome(1, 1, 0)):
        for _ in range(25):
            created = manager.create(make_request(tmp_path))
            deadline = monotonic() + 2
            while (
                manager.get(created["id"]) is not None
                and manager.get(created["id"])["state"] in {"queued", "running"}
                and monotonic() < deadline
            ):
                sleep(0.005)

        deadline = monotonic() + 2
        while manager.snapshot()["counts"]["running"] and monotonic() < deadline:
            sleep(0.005)

    persisted = state_path.read_text(encoding="utf-8")
    assert persisted.count('"sequence"') == 20
    assert "PL123" not in persisted


def test_manager_without_state_path_does_not_write_a_file(tmp_path: Path) -> None:
    manager = JobManager()
    with patch("playlist_audio.web.jobs.download") as mocked_download:
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        manager.create(make_request(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_manager_starts_empty_when_state_file_is_missing(tmp_path: Path) -> None:
    manager = JobManager(state_path=tmp_path / "missing" / "state.json")
    assert manager.snapshot() == {
        "active": None,
        "queued": [],
        "recent": [],
        "counts": {"running": 0, "queued": 0},
    }


def test_persists_a_queued_job_to_disk(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    manager = JobManager(state_path=state_path)
    with patch("playlist_audio.web.jobs.download") as mocked_download:
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        manager.create(make_request(tmp_path))
    assert state_path.is_file()


def test_restores_and_resumes_queue_after_restart(tmp_path: Path) -> None:
    """Simulate the app closing mid-download with a second job still queued."""
    state_path = tmp_path / "state.json"
    first_started = Event()
    release_first = Event()

    def blocking_download(request, progress_hook=None) -> DownloadOutcome:
        first_started.set()
        assert release_first.wait(timeout=2)
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    with patch("playlist_audio.web.jobs.download", side_effect=blocking_download):
        manager1 = JobManager(state_path=state_path)
        active = manager1.create(make_request(tmp_path))
        assert first_started.wait(timeout=2)
        queued = manager1.create(make_request(tmp_path))

        # Capture the on-disk state at the moment the app "closed", then let
        # manager1 wind down cleanly so its worker thread can't keep running
        # in the background and interfere with later tests.
        closed_state = state_path.read_bytes()
        manager1.cancel(queued["id"])
        release_first.set()
        deadline = monotonic() + 2
        while manager1.get(active["id"])["state"] == "running" and monotonic() < deadline:
            sleep(0.01)

    state_path.write_bytes(closed_state)

    def fake_download(request, progress_hook=None) -> DownloadOutcome:
        return DownloadOutcome(total_items=1, available_items=1, unavailable_items=0)

    with patch("playlist_audio.web.jobs.download", side_effect=fake_download):
        manager2 = JobManager(state_path=state_path)

        restored_active = manager2.get(active["id"])
        assert restored_active is not None
        assert restored_active["state"] == "failed"
        assert "Interrupted" in restored_active["message"]

        deadline = monotonic() + 2
        while manager2.get(queued["id"])["state"] != "completed" and monotonic() < deadline:
            sleep(0.01)
        assert manager2.get(queued["id"])["state"] == "completed"
        assert "PL123" not in state_path.read_text(encoding="utf-8")


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
