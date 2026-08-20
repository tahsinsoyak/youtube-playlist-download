"""Job state models shared by the local queue and HTTP API."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playlist_audio.models import Browser, DownloadRequest


def now_iso() -> str:
    """Return a sortable UTC timestamp for UI snapshots."""
    return datetime.now(UTC).isoformat()


def _request_to_dict(request: DownloadRequest) -> dict[str, Any]:
    return {
        "url": request.url,
        "output_dir": str(request.output_dir),
        "archive_file": str(request.archive_file),
        "browser": request.browser.value if request.browser else None,
        "browser_profile": request.browser_profile,
        "audio_quality": request.audio_quality,
        "audio_format": request.audio_format,
        "playlist_items": request.playlist_items,
        "dry_run": request.dry_run,
        "embed_thumbnail": request.embed_thumbnail,
        "embed_metadata": request.embed_metadata,
    }


def _request_from_dict(data: dict[str, Any]) -> DownloadRequest:
    browser_value = data.get("browser")
    return DownloadRequest(
        url=data["url"],
        output_dir=Path(data["output_dir"]),
        archive_file=Path(data["archive_file"]),
        browser=Browser(browser_value) if browser_value else None,
        browser_profile=data.get("browser_profile"),
        audio_quality=data.get("audio_quality", "0"),
        audio_format=data.get("audio_format", "mp3"),
        playlist_items=data.get("playlist_items"),
        dry_run=data.get("dry_run", False),
        embed_thumbnail=data.get("embed_thumbnail", True),
        embed_metadata=data.get("embed_metadata", True),
    )


@dataclass(slots=True)
class Job:
    """Mutable internal state guarded by the manager lock."""

    id: str
    sequence: int
    request: DownloadRequest
    state: str = "queued"
    progress: float | None = None
    message: str = "Added to queue"
    current_item: str | None = None
    playlist_title: str | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    item_index: int | None = None
    item_count: int | None = None
    available_items: int | None = None
    unavailable_items: int = 0
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
            "available_items": self.available_items,
            "unavailable_items": self.unavailable_items,
            "queue_position": queue_position,
            "dry_run": self.request.dry_run,
            "output": str(self.request.output_dir.resolve()),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def to_state_dict(self) -> dict[str, Any]:
        """Serialize full job state, including the source request, for local persistence."""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "request": _request_to_dict(self.request),
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
            "available_items": self.available_items,
            "unavailable_items": self.unavailable_items,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any]) -> "Job":
        """Reconstruct a Job from to_state_dict() output."""
        return cls(
            id=data["id"],
            sequence=data["sequence"],
            request=_request_from_dict(data["request"]),
            state=data.get("state", "queued"),
            progress=data.get("progress"),
            message=data.get("message", "Added to queue"),
            current_item=data.get("current_item"),
            playlist_title=data.get("playlist_title"),
            downloaded_bytes=data.get("downloaded_bytes", 0),
            total_bytes=data.get("total_bytes"),
            speed=data.get("speed"),
            eta=data.get("eta"),
            item_index=data.get("item_index"),
            item_count=data.get("item_count"),
            available_items=data.get("available_items"),
            unavailable_items=data.get("unavailable_items", 0),
            created_at=data.get("created_at") or now_iso(),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
        )
