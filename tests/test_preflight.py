from playlist_audio.preflight import run_checks


def test_preflight_has_expected_components() -> None:
    checks = run_checks()
    names = {check.name for check in checks}

    assert names == {"Python", "yt-dlp", "JavaScript", "FFmpeg", "ffprobe"}
    assert all(check.detail for check in checks)
