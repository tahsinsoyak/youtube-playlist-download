from playlist_audio.preflight import Check, readiness_error, readiness_status, run_checks


def test_preflight_has_expected_components() -> None:
    checks = run_checks()
    names = {check.name for check in checks}

    assert names == {"Python", "yt-dlp", "JavaScript", "FFmpeg", "ffprobe"}
    assert all(check.detail for check in checks)


def test_readiness_distinguishes_preview_from_conversion() -> None:
    checks = [
        Check("Python", True, "3.12"),
        Check("yt-dlp", True, "2026.8.19"),
        Check("JavaScript", True, "node 24"),
        Check("FFmpeg", False, "Not found"),
        Check("ffprobe", False, "Not found"),
    ]

    status = readiness_status(checks)

    assert status["preview_ready"] is True
    assert status["download_ready"] is False
    assert readiness_error(dry_run=True, status=status) is None
    assert "FFmpeg, ffprobe" in readiness_error(dry_run=False, status=status)
