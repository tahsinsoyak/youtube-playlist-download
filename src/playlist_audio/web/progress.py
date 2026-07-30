"""Translate yt-dlp progress events into stable UI fields."""

from typing import Any


def _positive_number(value: object) -> float | None:
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return None


def _positive_integer(value: object) -> int | None:
    number = _positive_number(value)
    return int(number) if number is not None else None


def _overall_progress(
    downloaded: int,
    total: int | None,
    item_index: int | None,
    item_count: int | None,
    *,
    item_finished: bool = False,
) -> float | None:
    if total:
        item_fraction = min(downloaded / total, 1)
    elif item_finished:
        item_fraction = 1
    else:
        return None

    if item_index and item_count:
        return min(((item_index - 1) + item_fraction) / item_count * 100, 100)
    return item_fraction * 100


def progress_changes(event: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded update from a yt-dlp progress-hook event."""
    status = event.get("status")
    info = event.get("info_dict") or {}
    total = _positive_integer(event.get("total_bytes")) or _positive_integer(
        event.get("total_bytes_estimate")
    )
    downloaded = _positive_integer(event.get("downloaded_bytes")) or 0
    item_index = _positive_integer(info.get("playlist_index"))
    item_count = _positive_integer(info.get("n_entries")) or _positive_integer(
        info.get("playlist_count")
    )
    changes: dict[str, Any] = {
        "current_item": info.get("title"),
        "playlist_title": info.get("playlist_title") or info.get("playlist"),
        "downloaded_bytes": downloaded,
        "total_bytes": total,
        "item_index": item_index,
        "item_count": item_count,
    }

    if status == "downloading":
        changes.update(
            progress=_overall_progress(downloaded, total, item_index, item_count),
            speed=_positive_number(event.get("speed")),
            eta=_positive_integer(event.get("eta")),
            message="Ses akışı indiriliyor",
        )
    elif status == "finished":
        changes.update(
            progress=_overall_progress(
                downloaded,
                total,
                item_index,
                item_count,
                item_finished=True,
            ),
            speed=None,
            eta=None,
            message="MP3 hazırlanıyor ve etiketleniyor",
        )
    return changes
