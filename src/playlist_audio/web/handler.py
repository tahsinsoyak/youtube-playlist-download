"""HTTP request handling for the local-only UI."""

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from playlist_audio.web.jobs import JobManager
from playlist_audio.web.request_parser import RequestError, parse_download_request

MAX_BODY_BYTES = 64 * 1024
ASSET_PACKAGE = "playlist_audio.web.assets"


def make_handler(manager: JobManager) -> type[BaseHTTPRequestHandler]:
    """Bind one job manager to a request-handler class."""

    class LocalUIHandler(BaseHTTPRequestHandler):
        server_version = "PlaylistAudioLocal/0.1"

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/":
                self._serve_asset("index.html", "text/html; charset=utf-8")
            elif path == "/api/health":
                self._json(HTTPStatus.OK, {"status": "ok", "scope": "localhost"})
            elif path == "/api/jobs":
                self._json(HTTPStatus.OK, manager.snapshot())
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

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
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
                job = manager.create(request)
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON."})
            except RequestError as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            else:
                self._json(HTTPStatus.ACCEPTED, job)

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
