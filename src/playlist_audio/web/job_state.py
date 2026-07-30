"""Job state models shared by the local queue and HTTP API."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from playlist_audio.models import DownloadRequest


def now_iso() -> str:
    """Return a sortable UTC timestamp for UI snapshots."""
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class Job:
    """Mutable internal state guarded by the manager lock."""

    id: str
    sequence: int
    request: DownloadRequest
    state: str = "queued"
    progress: float | None = None
    message: str = "Sıraya alındı"
    current_item: str | None = None
    playlist_title: str | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    item_index: int | None = None
    item_count: int | None = None
    created_at: str = field(default_factory=now_iso)
    started_at: str | None = None
    finished_at: str | None = None

    def public(self, queue_position: int | None = None) -> dict[str, Any]:
        """Return UI-safe state without exposing the source URL."""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "state": self.state,
            "progress": self.progress,
            "message": self.message,
            "current_item": self.current_item,
            "playlist_title": self.playlist_title,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "speed": self.speed,
            "eta": self.eta,
            "item_index": self.item_index,
            "item_count": self.item_count,
            "queue_position": queue_position,
            "dry_run": self.request.dry_run,
            "output": str(self.request.output_dir.resolve()),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
