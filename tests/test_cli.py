from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from playlist_audio.cli import app
from playlist_audio.config import ConfigDefaults
from playlist_audio.downloader import DownloadOutcome
from playlist_audio.preflight import Check

runner = CliRunner()
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def test_help_exposes_expected_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "download" in result.stdout
    assert "doctor" in result.stdout
    assert "ui" in result.stdout


def test_version_uses_public_project_name() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "youtube-playlist-download 0.2.0" in result.stdout


def test_doctor_exits_cleanly_when_a_dependency_is_missing() -> None:
    checks = [Check("FFmpeg", False, "Not found")]
    with patch("playlist_audio.cli.run_checks", return_value=checks):
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "Reliable YouTube/audio processing is unavailable" in result.stdout
    assert result.exception is not None
    assert result.exception.__class__.__name__ == "SystemExit"


def test_download_requires_rights_confirmation() -> None:
    result = runner.invoke(app, ["download", PLAYLIST_URL])

    assert result.exit_code == 2
    assert "--confirm-rights" in result.stdout


def test_dry_run_builds_request_without_network(tmp_path: Path) -> None:
    with patch("playlist_audio.cli.download") as mocked_download:
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        result = runner.invoke(
            app,
            [
                "download",
                PLAYLIST_URL,
                "--output",
                str(tmp_path),
                "--browser",
                "firefox",
                "--dry-run",
                "--confirm-rights",
            ],
        )

    assert result.exit_code == 0
    request = mocked_download.call_args.args[0]
    assert request.dry_run is True
    assert request.browser.value == "firefox"
    assert request.output_dir == tmp_path
    assert request.audio_format == "mp3"


def test_audio_format_flag_is_validated_and_applied(tmp_path: Path) -> None:
    with patch("playlist_audio.cli.download") as mocked_download:
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        result = runner.invoke(
            app,
            [
                "download",
                PLAYLIST_URL,
                "--output",
                str(tmp_path),
                "--audio-format",
                "m4a",
                "--dry-run",
                "--confirm-rights",
            ],
        )

    assert result.exit_code == 0
    request = mocked_download.call_args.args[0]
    assert request.audio_format == "m4a"


def test_rejects_unsupported_audio_format_flag() -> None:
    result = runner.invoke(
        app,
        ["download", PLAYLIST_URL, "--audio-format", "flac", "--confirm-rights"],
    )

    assert result.exit_code == 2
    assert "Invalid option" in result.stdout


def test_rejects_non_youtube_url() -> None:
    result = runner.invoke(
        app,
        ["download", "https://example.com/video", "--confirm-rights"],
    )

    assert result.exit_code == 2
    assert "Invalid option" in result.stdout


def test_ui_command_starts_local_server_without_opening_browser() -> None:
    with patch("playlist_audio.web.server.run_ui") as mocked_run_ui:
        result = runner.invoke(app, ["ui", "--port", "8765", "--no-open"])

    assert result.exit_code == 0
    mocked_run_ui.assert_called_once_with(port=8765, open_browser=False)


def test_config_file_supplies_defaults_when_flags_are_omitted(tmp_path: Path) -> None:
    config = ConfigDefaults(output=str(tmp_path), browser="firefox", audio_quality="2")
    with (
        patch("playlist_audio.cli.load_config", return_value=config),
        patch("playlist_audio.cli.download") as mocked_download,
    ):
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        result = runner.invoke(app, ["download", PLAYLIST_URL, "--dry-run", "--confirm-rights"])

    assert result.exit_code == 0
    request = mocked_download.call_args.args[0]
    assert request.output_dir == tmp_path
    assert request.browser.value == "firefox"
    assert request.audio_quality == "2"


def test_explicit_flags_override_config_file(tmp_path: Path) -> None:
    config = ConfigDefaults(output="C:/should-not-be-used", browser="chrome")
    with (
        patch("playlist_audio.cli.load_config", return_value=config),
        patch("playlist_audio.cli.download") as mocked_download,
    ):
        mocked_download.return_value = DownloadOutcome(1, 1, 0)
        result = runner.invoke(
            app,
            [
                "download",
                PLAYLIST_URL,
                "--output",
                str(tmp_path),
                "--browser",
                "firefox",
                "--dry-run",
                "--confirm-rights",
            ],
        )

    assert result.exit_code == 0
    request = mocked_download.call_args.args[0]
    assert request.output_dir == tmp_path
    assert request.browser.value == "firefox"


def test_rejects_unknown_browser_from_config_file() -> None:
    config = ConfigDefaults(browser="not-a-real-browser")
    with patch("playlist_audio.cli.load_config", return_value=config):
        result = runner.invoke(app, ["download", PLAYLIST_URL, "--confirm-rights"])

    assert result.exit_code == 2
    assert "config file" in result.stdout


def test_ui_command_uses_config_port_when_flag_omitted() -> None:
    config = ConfigDefaults(port=9100)
    with (
        patch("playlist_audio.cli.load_config", return_value=config),
        patch("playlist_audio.web.server.run_ui") as mocked_run_ui,
    ):
        result = runner.invoke(app, ["ui", "--no-open"])

    assert result.exit_code == 0
    mocked_run_ui.assert_called_once_with(port=9100, open_browser=False)
