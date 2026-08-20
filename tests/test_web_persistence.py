from pathlib import Path

from playlist_audio.models import Browser, DownloadRequest
from playlist_audio.web.job_state import Job
from playlist_audio.web.persistence import load_jobs, save_jobs


def make_job(tmp_path: Path, **overrides: object) -> Job:
    request = DownloadRequest(
        url="https://www.youtube.com/playlist?list=PL123",
        output_dir=tmp_path / "music",
        archive_file=tmp_path / "music" / ".playlist-audio-archive.txt",
        browser=Browser.FIREFOX,
        browser_profile="default-release",
        audio_format="opus",
        dry_run=True,
    )
    values: dict[str, object] = {"id": "job-1", "sequence": 1, "request": request}
    values.update(overrides)
    return Job(**values)  # type: ignore[arg-type]


def test_round_trips_job_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "queue-state.json"
    job = make_job(tmp_path, state="queued")

    save_jobs(state_path, [job], next_sequence=2)
    loaded = load_jobs(state_path)

    assert loaded is not None
    jobs, next_sequence = loaded
    assert next_sequence == 2
    assert len(jobs) == 1
    restored = jobs[0]
    assert restored.id == job.id
    assert restored.state == "queued"
    assert restored.request.url == job.request.url
    assert restored.request.output_dir == job.request.output_dir
    assert restored.request.browser == Browser.FIREFOX
    assert restored.request.browser_profile == "default-release"
    assert restored.request.audio_format == "opus"
    assert restored.request.dry_run is True


def test_load_returns_none_when_file_is_missing(tmp_path: Path) -> None:
    assert load_jobs(tmp_path / "does-not-exist.json") is None


def test_load_returns_none_for_corrupted_file(tmp_path: Path) -> None:
    state_path = tmp_path / "queue-state.json"
    state_path.write_text("not valid json", encoding="utf-8")

    assert load_jobs(state_path) is None


def test_load_returns_none_for_unknown_version(tmp_path: Path) -> None:
    state_path = tmp_path / "queue-state.json"
    state_path.write_text('{"version": 999, "next_sequence": 1, "jobs": []}', encoding="utf-8")

    assert load_jobs(state_path) is None


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    state_path = tmp_path / "nested" / "dir" / "queue-state.json"

    save_jobs(state_path, [], next_sequence=1)

    assert state_path.is_file()
