"""Thread-safe single-job coordinator for the local UI."""

import logging
import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from playlist_audio.downloader import DownloadFailed, download
from playlist_audio.models import DownloadRequest

LOGGER = logging.getLogger(__name__)


class JobConflict(RuntimeError):
    """Raised when a second job is requested while one is running."""


@dataclass(slots=True)
class Job:
    """Mutable internal state guarded by the manager lock."""

    id: str
    request: DownloadRequest
    state: str = "queued"
    progress: float | None = None
    message: str = "Sıraya alındı"
    current_item: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def public(self) -> dict[str, Any]:
        """Return only UI-safe state; never expose the source URL."""
        return {
            "id": self.id,
            "state": self.state,
            "progress": self.progress,
            "message": self.message,
            "current_item": self.current_item,
            "dry_run": self.request.dry_run,
            "output": str(self.request.output_dir.resolve()),
            "created_at": self.created_at,
        }


class JobManager:
    """Run at most one yt-dlp job and expose bounded status snapshots."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._active_id: str | None = None
        self._lock = threading.Lock()

    def create(self, request: DownloadRequest) -> dict[str, Any]:
        with self._lock:
            if self._active_id:
                active = self._jobs.get(self._active_id)
                if active and active.state in {"queued", "running"}:
                    raise JobConflict("Önce devam eden işlemin tamamlanmasını bekleyin.")

            job = Job(id=secrets.token_urlsafe(12), request=request)
            self._jobs[job.id] = job
            self._active_id = job.id
            self._trim_history()

        threading.Thread(target=self._run, args=(job.id,), daemon=True).start()
        return job.public()

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.public() if job else None

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
        status = event.get("status")
        info = event.get("info_dict") or {}
        title = info.get("title")

        if status == "downloading":
            total = event.get("total_bytes") or event.get("total_bytes_estimate")
            downloaded = event.get("downloaded_bytes") or 0
            progress = min(downloaded / total * 100, 100) if total else None
            index = info.get("playlist_index")
            count = info.get("n_entries") or info.get("playlist_count")
            prefix = f"{index}/{count} · " if index and count else ""
            self._update(
                job_id,
                progress=progress,
                current_item=title,
                message=f"{prefix}Ses akışı indiriliyor",
            )
        elif status == "finished":
            self._update(
                job_id,
                progress=100,
                current_item=title,
                message="MP3 hazırlanıyor ve etiketleniyor",
            )

    def _run(self, job_id: str) -> None:
        with self._lock:
            request = self._jobs[job_id].request
        initial = (
            "Playlist erişimi kontrol ediliyor" if request.dry_run else "Playlist hazırlanıyor"
        )
        self._update(job_id, state="running", message=initial)

        try:
            download(request, progress_hook=lambda event: self._progress_hook(job_id, event))
        except DownloadFailed as error:
            self._update(
                job_id,
                state="failed",
                message=str(error)[:800],
                progress=None,
            )
        except Exception:
            LOGGER.exception("Local UI job failed")
            self._update(
                job_id,
                state="failed",
                message="Beklenmeyen bir yerel hata oluştu. Terminal çıktısını kontrol edin.",
                progress=None,
            )
        else:
            message = "Önizleme tamamlandı" if request.dry_run else "İndirme tamamlandı"
            self._update(job_id, state="completed", message=message, progress=100)
        finally:
            with self._lock:
                if self._active_id == job_id:
                    self._active_id = None
