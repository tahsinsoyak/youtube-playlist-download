"""Save and restore the local job queue and history across app restarts."""

import json
import logging
from pathlib import Path

from playlist_audio.web.job_state import Job

LOGGER = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path.home() / ".playlist-audio" / "queue-state.json"
STATE_VERSION = 1


def save_jobs(path: Path, jobs: list[Job], next_sequence: int) -> None:
    """Write jobs and the sequence counter to disk, replacing any prior state.

    Writes to a temporary file first and renames it into place so a crash or
    concurrent read never observes a partially written file.
    """
    payload = {
        "version": STATE_VERSION,
        "next_sequence": next_sequence,
        "jobs": [job.to_state_dict() for job in jobs],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload), encoding="utf-8")
    tmp_path.replace(path)


def load_jobs(path: Path) -> tuple[list[Job], int] | None:
    """Read previously saved jobs; return None if absent, unreadable, or unversioned."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    try:
        payload = json.loads(raw)
        if payload.get("version") != STATE_VERSION:
            return None
        jobs = [Job.from_state_dict(item) for item in payload["jobs"]]
        next_sequence = int(payload["next_sequence"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        LOGGER.warning("Ignoring unreadable job queue state at %s", path)
        return None
    return jobs, next_sequence
