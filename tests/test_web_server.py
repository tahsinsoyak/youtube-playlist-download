import json
import threading
from contextlib import contextmanager
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playlist_audio.web.server import create_server


class FakeManager:
    def get(self, job_id: str) -> dict[str, Any] | None:
        if job_id == "known":
            return {"id": "known", "state": "completed"}
        return None

    def create(self, request) -> dict[str, Any]:
        return {"id": "new-job", "state": "queued", "dry_run": request.dry_run}


@contextmanager
def running_server():
    server = create_server(0, manager=FakeManager())  # type: ignore[arg-type]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_serves_ui_health_and_security_headers() -> None:
    with running_server() as base_url:
        with urlopen(f"{base_url}/", timeout=2) as response:
            html = response.read().decode()
            assert "Playlist Audio" in html
            assert response.headers["X-Frame-Options"] == "DENY"

        with urlopen(f"{base_url}/api/health", timeout=2) as response:
            assert json.load(response)["scope"] == "localhost"


def test_accepts_same_origin_json_job() -> None:
    payload = json.dumps(
        {
            "url": "https://www.youtube.com/playlist?list=PL123",
            "output": "downloads",
            "dry_run": True,
            "confirm_rights": True,
        }
    ).encode()

    with running_server() as base_url:
        request = Request(
            f"{base_url}/api/jobs",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Origin": base_url},
        )
        with urlopen(request, timeout=2) as response:
            result = json.load(response)
            assert response.status == 202
            assert result["id"] == "new-job"


def test_rejects_cross_origin_job() -> None:
    with running_server() as base_url:
        request = Request(
            f"{base_url}/api/jobs",
            data=b"{}",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://attacker.example",
            },
        )
        try:
            urlopen(request, timeout=2)
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("Cross-origin request should be rejected")
