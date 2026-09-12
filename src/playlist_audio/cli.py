"""Typer command-line interface."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from playlist_audio import __version__
from playlist_audio.config import ConfigDefaults, load_config
from playlist_audio.downloader import DownloadFailed, download, output_location
from playlist_audio.models import Browser, DownloadRequest
from playlist_audio.options import default_archive_path
from playlist_audio.preflight import run_checks
from playlist_audio.terminal import configure_utf8_output
from playlist_audio.validation import (
    ValidationError,
    validate_audio_format,
    validate_audio_quality,
    validate_browser_profile,
    validate_youtube_url,
)

configure_utf8_output()

app = typer.Typer(
    name="youtube-playlist-download",
    help="Archive authorized YouTube playlists as high-quality MP3 using a UI or CLI.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"youtube-playlist-download {__version__}")
        raise typer.Exit()


def _resolve_browser(browser: Browser | None, config: ConfigDefaults) -> Browser | None:
    if browser is not None or not config.browser:
        return browser
    try:
        return Browser(config.browser)
    except ValueError as error:
        console.print(
            f"[red]Invalid option:[/red] Unknown browser '{config.browser}' in config file."
        )
        raise typer.Exit(code=2) from error


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """Archive authorized YouTube playlists on your local device."""


@app.command()
def doctor() -> None:
    """Check the Python, yt-dlp, JavaScript, and FFmpeg setup."""
    checks = run_checks()
    table = Table(title="System check")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Details")

    for check in checks:
        status = "[green]Ready[/green]" if check.ok else "[red]Missing[/red]"
        table.add_row(check.name, status, check.detail)
    console.print(table)

    if not all(check.ok for check in checks if check.required):
        console.print(
            "\n[red]Reliable YouTube/audio processing is unavailable "
            "while required components are missing.[/red]"
        )
        raise typer.Exit(code=1)


@app.command("ui")
def ui_command(
    port: Annotated[
        int | None,
        typer.Option("--port", help="Local interface port. Defaults to 8765 or the config file."),
    ] = None,
    no_open: Annotated[
        bool,
        typer.Option("--no-open", help="Do not open the browser automatically."),
    ] = False,
) -> None:
    """Start the lightweight local web interface."""
    config = load_config()
    resolved_port = port if port is not None else (config.port or 8765)
    if not 1024 <= resolved_port <= 65535:
        console.print("[red]Port must be between 1024 and 65535.[/red]")
        raise typer.Exit(code=2)

    from playlist_audio.web.server import run_ui

    try:
        run_ui(port=resolved_port, open_browser=not no_open)
    except OSError as error:
        console.print(f"[red]Could not start the interface:[/red] {error}")
        raise typer.Exit(code=1) from error


@app.command("download")
def download_command(
    url: Annotated[str, typer.Argument(help="YouTube video or playlist URL.")],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Root folder for the download library. Defaults to 'downloads'."
        ),
    ] = None,
    browser: Annotated[
        Browser | None,
        typer.Option("--browser", help="Signed-in browser for authorized private content."),
    ] = None,
    browser_profile: Annotated[
        str | None,
        typer.Option("--browser-profile", help="Optional browser profile name or path."),
    ] = None,
    audio_quality: Annotated[
        str | None,
        typer.Option("--audio-quality", help="FFmpeg VBR: 0 is best, 10 is lowest."),
    ] = None,
    audio_format: Annotated[
        str | None,
        typer.Option("--audio-format", help="Output codec: mp3, m4a, or opus. Defaults to mp3."),
    ] = None,
    playlist_items: Annotated[
        str | None,
        typer.Option("--playlist-items", help="Examples: 1:10, 1,3,7, or 10-."),
    ] = None,
    archive: Annotated[
        Path | None,
        typer.Option("--archive", help="Archive file used to prevent duplicates."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Check access and selection without writing media."),
    ] = False,
    no_thumbnail: Annotated[
        bool,
        typer.Option("--no-thumbnail", help="Do not embed cover art."),
    ] = False,
    no_metadata: Annotated[
        bool,
        typer.Option("--no-metadata", help="Do not embed title and artist metadata."),
    ] = False,
    confirm_rights: Annotated[
        bool,
        typer.Option(
            "--confirm-rights",
            help="Confirm that you are authorized to download the content.",
        ),
    ] = False,
) -> None:
    """Download one video or playlist as an audio file."""
    if not confirm_rights:
        console.print(
            "[red]Stopped:[/red] Use only content you are authorized to download. "
            "Add [bold]--confirm-rights[/bold] when you have permission."
        )
        raise typer.Exit(code=2)

    config = load_config()
    resolved_output = output or (Path(config.output) if config.output else Path("downloads"))
    resolved_browser = _resolve_browser(browser, config)
    resolved_browser_profile = browser_profile or config.browser_profile
    resolved_audio_quality = audio_quality or config.audio_quality or "0"
    resolved_audio_format = audio_format or config.audio_format or "mp3"

    try:
        validated_url = validate_youtube_url(url)
        validated_quality = validate_audio_quality(resolved_audio_quality)
        validated_format = validate_audio_format(resolved_audio_format)
        validate_browser_profile(resolved_browser, resolved_browser_profile)
    except ValidationError as error:
        console.print(f"[red]Invalid option:[/red] {error}")
        raise typer.Exit(code=2) from error

    output_dir = resolved_output.expanduser()
    request = DownloadRequest(
        url=validated_url,
        output_dir=output_dir,
        archive_file=(archive or default_archive_path(output_dir)).expanduser(),
        browser=resolved_browser,
        browser_profile=resolved_browser_profile,
        audio_quality=validated_quality,
        audio_format=validated_format,
        playlist_items=playlist_items,
        dry_run=dry_run,
        embed_thumbnail=not no_thumbnail,
        embed_metadata=not no_metadata,
    )

    if resolved_browser:
        console.print(
            f"The [cyan]{resolved_browser.value}[/cyan] session will be used. "
            "Close the browser completely if its cookie database is locked."
        )
    if dry_run:
        console.print("[yellow]Preview mode: no media file will be written.[/yellow]")

    try:
        outcome = download(request)
    except DownloadFailed as error:
        console.print(f"\n[red]Download could not be completed:[/red] {error}")
        raise typer.Exit(code=1) from error

    action = "Preview complete" if dry_run else "Download complete"
    console.print(f"\n[green]{action}.[/green] Destination: {output_location(request)}")
    if outcome.unavailable_items:
        console.print(
            f"[yellow]{outcome.unavailable_items} unavailable item(s) skipped; "
            f"{outcome.available_items} item(s) accessible.[/yellow]"
        )


if __name__ == "__main__":
    app()
