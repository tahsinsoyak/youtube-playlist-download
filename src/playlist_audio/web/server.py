"""Lifecycle for the loopback-only web server."""

import threading
import webbrowser
from http.server import ThreadingHTTPServer

from rich.console import Console

from playlist_audio.web.handler import make_handler
from playlist_audio.web.jobs import JobManager
from playlist_audio.web.persistence import DEFAULT_STATE_PATH

LOOPBACK_HOST = "127.0.0.1"


class LocalUIServer(ThreadingHTTPServer):
    """Threaded server that never binds to a public interface."""

    daemon_threads = True
    allow_reuse_address = True


def create_server(port: int, manager: JobManager | None = None) -> LocalUIServer:
    """Create a loopback server; port 0 is supported for tests."""
    return LocalUIServer((LOOPBACK_HOST, port), make_handler(manager or JobManager()))


def run_ui(port: int, open_browser: bool = True) -> None:
    """Run until Ctrl+C and optionally open the default browser."""
    console = Console()
    server = create_server(port, manager=JobManager(state_path=DEFAULT_STATE_PATH))
    actual_port = server.server_port
    url = f"http://{LOOPBACK_HOST}:{actual_port}"

    console.print("\n[bold]YouTube Playlist Download UI is ready.[/bold]")
    console.print(f"Address: [link={url}]{url}[/link]")
    console.print("Available only on this computer. Press Ctrl+C to stop.\n")

    if open_browser:
        threading.Timer(0.35, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping the interface…[/yellow]")
    finally:
        server.server_close()
