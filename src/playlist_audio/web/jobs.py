"""Thread-safe sequential download queue for the local UI."""

import logging
import secrets
import threading
from collections import deque
from pathlib import Path
from typing import Any

from playlist_audio.downloader import DownloadCancelled, DownloadFailed, download
from playlist_audio.models import DownloadRequest
from playlist_audio.web.job_state import Job, now_iso
from playlist_audio.web.persistence import load_jobs, save_jobs
from playlist_audio.web.progress import progress_changes

LOGGER = logging.getLogger(__name__)
MAX_PERSISTED_HISTORY = 20


class JobManager:
    """Accept many jobs while running exactly one yt-dlp worker at a time."""

    def __init__(self, state_path: Path | None = None) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: deque[str] = deque()
        self._active_id: str | None = None
        self._worker_running = False
        self._cancel_requested: set[str] = set()
        self._next_sequence = 1
        self._lock = threading.Lock()
        self._persist_lock = threading.Lock()
        self._state_path = state_path
        if state_path is not None:
            self._restore_state()

    def _restore_state(self) -> None:
        """Reload queued jobs and history saved before the app last closed."""
        loaded = load_jobs(self._state_path)
        if loaded is None:
            return
        jobs, next_sequence = loaded
        should_start = False
        state_changed = False
        with self._lock:
            for job in jobs:
                if job.state == "running":
                    job.state = "failed"
                    job.message = "Interrupted when the app was previously closed"
                    job.progress = None
                    job.speed = None
                    job.eta = None
                    job.finished_at = now_iso()
                    state_changed = True
                self._jobs[job.id] = job
                if job.state == "queued":
                    self._queue.append(job.id)
            self._next_sequence = max(next_sequence, self._next_sequence)
            if self._queue and not self._worker_running:
                self._worker_running = True
                should_start = True
        if state_changed:
            self._persist()
        if should_start:
            threading.Thread(target=self._work_queue, daemon=True).start()

    def _persist(self) -> None:
        if self._state_path is None:
            return
        # Snapshot only after this writer reaches the front of the line. This
        # prevents a delayed, older snapshot from replacing newer queue state.
        with self._persist_lock:
            with self._lock:
                jobs = list(self._jobs.values())
                next_sequence = self._next_sequence
            try:
                save_jobs(self._state_path, jobs, next_sequence)
            except OSError:
                LOGGER.warning("Could not persist job queue state", exc_info=True)

    def create(self, request: DownloadRequest) -> dict[str, Any]:
        with self._lock:
            job = Job(
                id=secrets.token_urlsafe(12),
                sequence=self._next_sequence,
                request=request,
            )
            self._next_sequence += 1
            self._jobs[job.id] = job
            self._queue.append(job.id)
            queue_position = len(self._queue)
            should_start = not self._worker_running
            if should_start:
                self._worker_running = True
            self._trim_history()

        if should_start:
            threading.Thread(target=self._work_queue, daemon=True).start()
        self._persist()
        return job.public(queue_position=queue_position)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return job.public(queue_position=self._queue_position(job_id))

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        """Cancel a queued job or ask the active yt-dlp operation to stop."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            if job.state == "running" and self._active_id == job_id:
                self._cancel_requested.add(job_id)
                job.message = "Cancellation requested"
                result = job.public()
            elif job.state == "queued":
                try:
                    self._queue.remove(job_id)
                except ValueError:
                    return None
                job.state = "cancelled"
                job.message = "Cancelled before it started"
                job.finished_at = now_iso()
                self._trim_history()
                result = job.public()
            else:
                return None
        self._persist()
        return result

    def retry(self, job_id: str) -> dict[str, Any] | None:
        """Queue a new attempt for a failed or cancelled job from this session."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.state not in {"failed", "cancelled"} or not job.request.url:
                return None
            request = job.request
        return self.create(request)

    def snapshot(self) -> dict[str, Any]:
        """Return the active job, pending queue and bounded recent history."""
        with self._lock:
            active = self._jobs.get(self._active_id) if self._active_id else None
            queued = [
                self._jobs[job_id].public(queue_position=index)
                for index, job_id in enumerate(self._queue, start=1)
            ]
            recent_jobs = [
                job
                for job in self._jobs.values()
                if job.state in {"completed", "failed", "cancelled"}
            ][-5:]
            return {
                "active": active.public() if active else None,
                "queued": queued,
                "recent": [job.public() for job in reversed(recent_jobs)],
                "counts": {
                    "running": 1 if active else 0,
                    "queued": len(queued),
                },
            }

    def _queue_position(self, job_id: str) -> int | None:
        try:
            return self._queue.index(job_id) + 1
        except ValueError:
            return None

    def _trim_history(self) -> None:
        completed = [
            job_id for job_id, job in self._jobs.items() if job.state not in {"queued", "running"}
        ]
        for job_id in completed[:-MAX_PERSISTED_HISTORY]:
            self._jobs.pop(job_id, None)

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)

    def _progress_hook(self, job_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            if job_id in self._cancel_requested:
                raise DownloadCancelled("Download cancelled")
        changes = progress_changes(event)
        if changes:
            self._update(job_id, **changes)

    def _cancel_was_requested(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._cancel_requested

    def _mark_cancelled(self, job_id: str) -> None:
        self._update(
            job_id,
            state="cancelled",
            message="Download cancelled",
            progress=None,
            speed=None,
            eta=None,
            finished_at=now_iso(),
        )

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            request = self._jobs[job_id].request
        initial = "Checking access" if request.dry_run else "Preparing download"
        self._update(job_id, state="running", message=initial, started_at=now_iso())
        self._persist()

        try:
            outcome = download(
                request,
                progress_hook=lambda event: self._progress_hook(job_id, event),
            )
        except DownloadCancelled:
            self._mark_cancelled(job_id)
        except DownloadFailed as error:
            if self._cancel_was_requested(job_id):
                self._mark_cancelled(job_id)
            else:
                self._update(
                    job_id,
                    state="failed",
                    message=str(error)[:800],
                    progress=None,
                    speed=None,
                    eta=None,
                    finished_at=now_iso(),
                )
        except Exception:
            LOGGER.exception("Local UI job failed")
            self._update(
                job_id,
                state="failed",
                message="An unexpected local error occurred. Check the terminal output.",
                progress=None,
                speed=None,
                eta=None,
                finished_at=now_iso(),
            )
        else:
            if self._cancel_was_requested(job_id):
                self._mark_cancelled(job_id)
            else:
                message = "Preview complete" if request.dry_run else "Download complete"
                if outcome and outcome.unavailable_items:
                    message = (
                        f"{message} · {outcome.available_items} accessible, "
                        f"{outcome.unavailable_items} unavailable item(s) skipped"
                    )
                self._update(
                    job_id,
                    state="completed",
                    message=message,
                    progress=100,
                    speed=None,
                    eta=0,
                    available_items=outcome.available_items if outcome else None,
                    unavailable_items=outcome.unavailable_items if outcome else 0,
                    finished_at=now_iso(),
                )
        with self._lock:
            self._cancel_requested.discard(job_id)
            self._trim_history()
        self._persist()

    def _work_queue(self) -> None:
        while True:
            with self._lock:
                if not self._queue:
                    self._active_id = None
                    self._worker_running = False
                    return
                job_id = self._queue.popleft()
                self._active_id = job_id
            self._run_job(job_id)
            with self._lock:
                if self._active_id == job_id:
                    self._active_id = None
