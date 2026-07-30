from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from playlist_audio.cli import app

runner = CliRunner()
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def test_help_exposes_expected_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "download" in result.stdout
    assert "doctor" in result.stdout
    assert "ui" in result.stdout


def test_download_requires_rights_confirmation() -> None:
    result = runner.invoke(app, ["download", PLAYLIST_URL])

    assert result.exit_code == 2
    assert "--confirm-rights" in result.stdout


def test_dry_run_builds_request_without_network(tmp_path: Path) -> None:
    with patch("playlist_audio.cli.download") as mocked_download:
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


def test_rejects_non_youtube_url() -> None:
    result = runner.invoke(
        app,
        ["download", "https://example.com/video", "--confirm-rights"],
    )

    assert result.exit_code == 2
    assert "Geçersiz seçenek" in result.stdout


def test_ui_command_starts_local_server_without_opening_browser() -> None:
    with patch("playlist_audio.web.server.run_ui") as mocked_run_ui:
        result = runner.invoke(app, ["ui", "--port", "8765", "--no-open"])

    assert result.exit_code == 0
    mocked_run_ui.assert_called_once_with(port=8765, open_browser=False)
