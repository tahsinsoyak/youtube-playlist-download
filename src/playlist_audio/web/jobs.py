"""Thread-safe sequential download queue for the local UI."""

import logging
import secrets
import threading
from collections import deque
from typing import Any

from playlist_audio.downloader import DownloadFailed, download
from playlist_audio.models import DownloadRequest
from playlist_audio.web.job_state import Job, now_iso
from playlist_audio.web.progress import progress_changes

LOGGER = logging.getLogger(__name__)


class JobManager:
    """Accept many jobs while running exactly one yt-dlp worker at a time."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: deque[str] = deque()
        self._active_id: str | None = None
        self._worker_running = False
        self._next_sequence = 1
        self._lock = threading.Lock()

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
        return job.public(queue_position=queue_position)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return job.public(queue_position=self._queue_position(job_id))

    def snapshot(self) -> dict[str, Any]:
        """Return the active job, pending queue and bounded recent history."""
        with self._lock:
            active = self._jobs.get(self._active_id) if self._active_id else None
            queued = [
                self._jobs[job_id].public(queue_position=index)
                for index, job_id in enumerate(self._queue, start=1)
            ]
            recent_jobs = [
                job for job in self._jobs.values() if job.state in {"completed", "failed"}
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
        for job_id in completed[:-19]:
            self._jobs.pop(job_id, None)

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)

    def _progress_hook(self, job_id: str, event: dict[str, Any]) -> None:
        changes = progress_changes(event)
        if changes:
            self._update(job_id, **changes)

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            request = self._jobs[job_id].request
        initial = (
            "Playlist erişimi kontrol ediliyor" if request.dry_run else "Playlist hazırlanıyor"
        )
        self._update(job_id, state="running", message=initial, started_at=now_iso())

        try:
            outcome = download(
                request,
                progress_hook=lambda event: self._progress_hook(job_id, event),
            )
        except DownloadFailed as error:
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
                message="Beklenmeyen bir yerel hata oluştu. Terminal çıktısını kontrol edin.",
                progress=None,
                speed=None,
                eta=None,
                finished_at=now_iso(),
            )
        else:
            message = "Önizleme tamamlandı" if request.dry_run else "İndirme tamamlandı"
            if outcome and outcome.unavailable_items:
                message = (
                    f"{message} · {outcome.available_items} erişilebilir, "
                    f"{outcome.unavailable_items} kullanılamayan öğe atlandı"
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
