"""Typer command-line interface."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from playlist_audio import __version__
from playlist_audio.downloader import DownloadFailed, download, output_location
from playlist_audio.models import Browser, DownloadRequest
from playlist_audio.options import default_archive_path
from playlist_audio.preflight import run_checks
from playlist_audio.terminal import configure_utf8_output
from playlist_audio.validation import (
    ValidationError,
    validate_audio_quality,
    validate_browser_profile,
    validate_youtube_url,
)

configure_utf8_output()

app = typer.Typer(
    name="playlist-audio",
    help="İzinli YouTube playlistlerini yüksek kaliteli MP3 olarak arşivler.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"playlist-audio {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """İzinli YouTube playlistlerini yerel cihazınızda arşivleyin."""


@app.command()
def doctor() -> None:
    """Python, yt-dlp ve FFmpeg kurulumunu kontrol eder."""
    checks = run_checks()
    table = Table(title="Sistem kontrolü")
    table.add_column("Bileşen")
    table.add_column("Durum")
    table.add_column("Ayrıntı")

    for check in checks:
        status = "[green]Hazır[/green]" if check.ok else "[red]Eksik[/red]"
        table.add_row(check.name, status, check.detail)
    console.print(table)

    if not all(check.ok for check in checks if check.required):
        console.print(
            "\n[red]Eksik zorunlu bileşenlerle güvenilir",
            "YouTube/MP3 işlemi yapılamaz.[/red]",
        )
        raise typer.Exit(code=1)


@app.command("ui")
def ui_command(
    port: Annotated[
        int,
        typer.Option("--port", help="Yerel arayüz portu."),
    ] = 8765,
    no_open: Annotated[
        bool,
        typer.Option("--no-open", help="Tarayıcıyı otomatik açma."),
    ] = False,
) -> None:
    """Hafif yerel web arayüzünü başlatır."""
    if not 1024 <= port <= 65535:
        console.print("[red]Port 1024 ile 65535 arasında olmalıdır.[/red]")
        raise typer.Exit(code=2)

    from playlist_audio.web.server import run_ui

    try:
        run_ui(port=port, open_browser=not no_open)
    except OSError as error:
        console.print(f"[red]Arayüz başlatılamadı:[/red] {error}")
        raise typer.Exit(code=1) from error


@app.command("download")
def download_command(
    url: Annotated[str, typer.Argument(help="YouTube video veya playlist URL'si.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="İndirme kitaplığının kök klasörü."),
    ] = Path("downloads"),
    browser: Annotated[
        Browser | None,
        typer.Option("--browser", help="Private içerik için oturum açık tarayıcı."),
    ] = None,
    browser_profile: Annotated[
        str | None,
        typer.Option("--browser-profile", help="İsteğe bağlı tarayıcı profil adı/yolu."),
    ] = None,
    audio_quality: Annotated[
        str,
        typer.Option("--audio-quality", help="FFmpeg VBR: 0 en iyi, 10 en düşük."),
    ] = "0",
    playlist_items: Annotated[
        str | None,
        typer.Option("--playlist-items", help="Örn. 1:10, 1,3,7 veya 10-."),
    ] = None,
    archive: Annotated[
        Path | None,
        typer.Option("--archive", help="Tekrar indirmeyi önleyen arşiv dosyası."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Dosya indirmeden erişimi ve seçimi denetle."),
    ] = False,
    no_thumbnail: Annotated[
        bool,
        typer.Option("--no-thumbnail", help="Kapak görseli gömme."),
    ] = False,
    no_metadata: Annotated[
        bool,
        typer.Option("--no-metadata", help="Başlık/sanatçı metadata'sı gömme."),
    ] = False,
    confirm_rights: Annotated[
        bool,
        typer.Option(
            "--confirm-rights",
            help="İçeriği indirme yetkiniz olduğunu onaylayın.",
        ),
    ] = False,
) -> None:
    """Bir video veya playlisti MP3 olarak indirir."""
    if not confirm_rights:
        console.print(
            "[red]Durduruldu:[/red] Yalnızca indirme hakkınız olan içerikleri kullanın. "
            "Yetkiniz varsa [bold]--confirm-rights[/bold] ekleyin."
        )
        raise typer.Exit(code=2)

    try:
        validated_url = validate_youtube_url(url)
        validated_quality = validate_audio_quality(audio_quality)
        validate_browser_profile(browser, browser_profile)
    except ValidationError as error:
        console.print(f"[red]Geçersiz seçenek:[/red] {error}")
        raise typer.Exit(code=2) from error

    output_dir = output.expanduser()
    request = DownloadRequest(
        url=validated_url,
        output_dir=output_dir,
        archive_file=(archive or default_archive_path(output_dir)).expanduser(),
        browser=browser,
        browser_profile=browser_profile,
        audio_quality=validated_quality,
        playlist_items=playlist_items,
        dry_run=dry_run,
        embed_thumbnail=not no_thumbnail,
        embed_metadata=not no_metadata,
    )

    if browser:
        console.print(
            f"[cyan]{browser.value}[/cyan] oturumu kullanılacak. "
            "Tarayıcı kilit hatası alırsanız tarayıcıyı tamamen kapatın."
        )
    if dry_run:
        console.print("[yellow]Önizleme modu: medya dosyası yazılmayacak.[/yellow]")

    try:
        outcome = download(request)
    except DownloadFailed as error:
        console.print(f"\n[red]İndirme tamamlanamadı:[/red] {error}")
        raise typer.Exit(code=1) from error

    action = "Önizleme tamamlandı" if dry_run else "İndirme tamamlandı"
    console.print(f"\n[green]{action}.[/green] Hedef: {output_location(request)}")
    if outcome.unavailable_items:
        console.print(
            f"[yellow]{outcome.unavailable_items} kullanılamayan öğe atlandı; "
            f"{outcome.available_items} öğe erişilebilir.[/yellow]"
        )


if __name__ == "__main__":
    app()
