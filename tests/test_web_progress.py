from playlist_audio.web.progress import progress_changes


def test_progress_event_includes_overall_playlist_metrics() -> None:
    changes = progress_changes(
        {
            "status": "downloading",
            "downloaded_bytes": 50,
            "total_bytes": 100,
            "speed": 128_000.5,
            "eta": 12,
            "info_dict": {
                "title": "Current song",
                "playlist_title": "Archive",
                "playlist_index": 2,
                "playlist_count": 4,
            },
        }
    )

    assert changes == {
        "current_item": "Current song",
        "playlist_title": "Archive",
        "downloaded_bytes": 50,
        "total_bytes": 100,
        "item_index": 2,
        "item_count": 4,
        "progress": 37.5,
        "speed": 128_000.5,
        "eta": 12,
        "message": "Downloading audio stream",
    }


def test_finished_event_advances_playlist_without_claiming_full_completion() -> None:
    changes = progress_changes(
        {
            "status": "finished",
            "downloaded_bytes": 100,
            "total_bytes": 100,
            "info_dict": {"playlist_index": 3, "playlist_count": 10},
        }
    )

    assert changes["progress"] == 30
    assert changes["speed"] is None
    assert changes["eta"] is None
