"""HTTP request handling for the local-only UI."""

import json
import mimetypes
import os
import platform
import subprocess
from contextlib import suppress
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playlist_audio.preflight import readiness_error, readiness_status
from playlist_audio.web.jobs import JobManager
from playlist_audio.web.request_parser import RequestError, parse_download_request

MAX_BODY_BYTES = 64 * 1024
ASSET_PACKAGE = "playlist_audio.web.assets"


def open_directory(path: Path) -> bool:
    """Reveal or open a directory in the native file explorer."""
    if not path.is_dir():
        return False
    try:
        if hasattr(os, "startfile"):
            os.startfile(str(path))
            return True
        current_os = platform.system()
        if current_os == "Darwin":
            subprocess.Popen(["open", str(path)])
            return True
        subprocess.Popen(["xdg-open", str(path)])
        return True
    except OSError:
        return False


def make_handler(
    manager: JobManager,
    health: dict[str, object] | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Bind one job manager to a request-handler class."""
    current_health = health if health is not None else readiness_status()

    class LocalUIHandler(BaseHTTPRequestHandler):
        server_version = "PlaylistAudioLocal/0.1"

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/":
                self._serve_asset("index.html", "text/html; charset=utf-8")
            elif path == "/api/health":
                self._json(HTTPStatus.OK, current_health)
            elif path == "/api/jobs":
                self._json(HTTPStatus.OK, manager.snapshot())
            elif path == "/api/jobs/export":
                self._json_download(manager.snapshot(), "job-history.json")
            elif path.startswith("/api/jobs/"):
                job_id = path.removeprefix("/api/jobs/")
                job = manager.get(job_id)
                if job:
                    self._json(HTTPStatus.OK, job)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Job not found."})
            elif path.startswith("/assets/"):
                asset_name = path.removeprefix("/assets/")
                if "/" in asset_name or "\\" in asset_name or ".." in asset_name:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "File not found."})
                    return
                content_type = mimetypes.guess_type(asset_name)[0] or "application/octet-stream"
                if content_type.startswith(("text/", "application/javascript")):
                    content_type = f"{content_type}; charset=utf-8"
                self._serve_asset(asset_name, content_type)
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Page not found."})

        def do_DELETE(self) -> None:  # noqa: N802
            self._drain_body()
            if not self._is_local_json_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Local request validation failed."})
                return
            path = urlsplit(self.path).path
            if path == "/api/jobs/history":
                cleared = manager.clear_history()
                self._json(HTTPStatus.OK, {"cleared": cleared})
                return
            if not path.startswith("/api/jobs/"):
                self._json(HTTPStatus.NOT_FOUND, {"error": "Page not found."})
                return
            job_id = path.removeprefix("/api/jobs/")
            if manager.get(job_id) is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Job not found."})
                return
            cancelled = manager.cancel(job_id)
            if cancelled:
                self._json(HTTPStatus.OK, cancelled)
            else:
                self._json(
                    HTTPStatus.CONFLICT,
                    {"error": "Job cannot be cancelled; it may have already started."},
                )

        def _drain_body(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if 0 < length <= MAX_BODY_BYTES:
                with suppress(OSError):
                    self.rfile.read(length)

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path.startswith("/api/jobs/") and path.endswith("/retry"):
                self._retry_job(path.removeprefix("/api/jobs/").removesuffix("/retry"))
                return
            if path.startswith("/api/jobs/") and path.endswith("/open-folder"):
                self._open_job_folder(path.removeprefix("/api/jobs/").removesuffix("/open-folder"))
                return
            if path != "/api/jobs":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Page not found."})
                return
            if not self._is_local_json_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Local request validation failed."})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                content_length = 0
            if content_length <= 0 or content_length > MAX_BODY_BYTES:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid request size."})
                return

            try:
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise RequestError("Expected a JSON object.")
                request = parse_download_request(payload)
                setup_error = readiness_error(dry_run=request.dry_run, status=current_health)
                if setup_error:
                    self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": setup_error})
                    return
                job = manager.create(request)
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON."})
            except RequestError as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            else:
                self._json(HTTPStatus.ACCEPTED, job)

        def _retry_job(self, job_id: str) -> None:
            self._drain_body()
            if not self._is_local_json_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Local request validation failed."})
                return
            existing = manager.get(job_id)
            if existing is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Job not found."})
                return
            setup_error = readiness_error(
                dry_run=bool(existing.get("dry_run")),
                status=current_health,
            )
            if setup_error:
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": setup_error})
                return
            retried = manager.retry(job_id)
            if retried:
                self._json(HTTPStatus.ACCEPTED, retried)
            else:
                self._json(
                    HTTPStatus.CONFLICT,
                    {"error": "This job cannot be retried after restart or while it is active."},
                )

        def _open_job_folder(self, job_id: str) -> None:
            self._drain_body()
            if not self._is_local_json_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Local request validation failed."})
                return
            existing = manager.get(job_id)
            if existing is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Job not found."})
                return
            if existing.get("dry_run"):
                self._json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Safe preview jobs do not create output folders."},
                )
                return
            output_raw = str(existing.get("output", "")).strip()
            if not output_raw:
                self._json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "Output directory not specified."},
                )
                return
            output_path = Path(output_raw).resolve()
            if not output_path.is_dir():
                self._json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "Output directory does not exist on disk."},
                )
                return
            if not open_directory(output_path):
                self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "Could not open folder in file manager."},
                )
                return
            self._json(HTTPStatus.OK, {"ok": True, "path": str(output_path)})

        def _is_local_json_request(self) -> bool:
            port = self.server.server_port  # type: ignore[attr-defined]
            allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            host = self.headers.get("Host", "").lower()
            origin = self.headers.get("Origin")
            allowed_origins = {f"http://{item}" for item in allowed_hosts}
            content_type = self.headers.get("Content-Type", "")
            return (
                host in allowed_hosts
                and (not origin or origin.lower() in allowed_origins)
                and content_type.split(";", 1)[0].strip() == "application/json"
            )

        def _serve_asset(self, name: str, content_type: str) -> None:
            try:
                content = files(ASSET_PACKAGE).joinpath(name).read_bytes()
            except (FileNotFoundError, IsADirectoryError):
                self._json(HTTPStatus.NOT_FOUND, {"error": "File not found."})
                return

            self.send_response(HTTPStatus.OK)
            self._security_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self._security_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _json_download(self, payload: dict[str, Any], filename: str) -> None:
            content = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            self.send_response(HTTPStatus.OK)
            self._security_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _security_headers(self) -> None:
            self.close_connection = True
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                "base-uri 'none'; form-action 'self'",
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")

        def log_message(self, format: str, *args: object) -> None:
            """Keep private URLs and local job identifiers out of access logs."""

    return LocalUIHandler
