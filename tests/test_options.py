from pathlib import Path

from playlist_audio.models import Browser, DownloadRequest
from playlist_audio.options import build_ydl_options, default_archive_path


def make_request(tmp_path: Path, **overrides: object) -> DownloadRequest:
    values: dict[str, object] = {
        "url": "https://www.youtube.com/playlist?list=PL123",
        "output_dir": tmp_path / "music",
        "archive_file": tmp_path / "music" / ".playlist-audio-archive.txt",
    }
    values.update(overrides)
    return DownloadRequest(**values)  # type: ignore[arg-type]


def test_builds_high_quality_mp3_options(tmp_path: Path) -> None:
    options = build_ydl_options(make_request(tmp_path))

    assert options["format"] == "bestaudio/best"
    assert options["download_archive"].endswith(".playlist-audio-archive.txt")
    assert options["writethumbnail"] is True
    assert isinstance(options["js_runtimes"], dict)
    assert options["postprocessors"][0] == {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "0",
    }


def test_private_playlist_uses_browser_without_cookie_file(tmp_path: Path) -> None:
    options = build_ydl_options(
        make_request(
            tmp_path,
            browser=Browser.FIREFOX,
            browser_profile="default-release",
        )
    )

    assert options["cookiesfrombrowser"] == (
        "firefox",
        "default-release",
        None,
        None,
    )
    assert "cookiefile" not in options


def test_can_disable_optional_embedding(tmp_path: Path) -> None:
    options = build_ydl_options(make_request(tmp_path, embed_thumbnail=False, embed_metadata=False))

    assert options["writethumbnail"] is False
    assert [item["key"] for item in options["postprocessors"]] == ["FFmpegExtractAudio"]


def test_default_archive_is_inside_output() -> None:
    assert default_archive_path(Path("library")) == Path("library/.playlist-audio-archive.txt")


def test_playlist_items_pass_through_when_set(tmp_path: Path) -> None:
    options = build_ydl_options(make_request(tmp_path, playlist_items="1:10"))

    assert options["playlist_items"] == "1:10"


def test_playlist_items_absent_when_not_set(tmp_path: Path) -> None:
    options = build_ydl_options(make_request(tmp_path))

    assert "playlist_items" not in options


def test_audio_format_selects_the_extraction_codec(tmp_path: Path) -> None:
    options = build_ydl_options(make_request(tmp_path, audio_format="opus"))

    assert options["postprocessors"][0]["preferredcodec"] == "opus"
