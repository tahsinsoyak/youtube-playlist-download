import json
import threading
from contextlib import contextmanager
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playlist_audio.web.server import create_server

READY_HEALTH = {
    "status": "ok",
    "scope": "localhost",
    "preview_ready": True,
    "download_ready": True,
    "checks": [
        {"name": name, "ok": True, "detail": "Ready"}
        for name in ("Python", "yt-dlp", "JavaScript", "FFmpeg", "ffprobe")
    ],
}


class FakeManager:
    def get(self, job_id: str) -> dict[str, Any] | None:
        if job_id == "known":
            return {"id": "known", "state": "completed"}
        if job_id == "queued":
            return {"id": "queued", "state": "queued"}
        return None

    def create(self, request) -> dict[str, Any]:
        return {"id": "new-job", "state": "queued", "dry_run": request.dry_run}

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        if job_id == "queued":
            return {"id": "queued", "state": "cancelled"}
        return None

    def retry(self, job_id: str) -> dict[str, Any] | None:
        if job_id == "known":
            return {"id": "retried-job", "state": "queued"}
        return None

    def snapshot(self) -> dict[str, Any]:
        return {
            "active": None,
            "queued": [],
            "recent": [],
            "counts": {"running": 0, "queued": 0},
        }


@contextmanager
def running_server(health: dict[str, object] | None = None):
    server = create_server(  # type: ignore[arg-type]
        0,
        manager=FakeManager(),
        health=health or READY_HEALTH,
    )
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
            assert "YouTube Playlist Download" in html
            assert response.headers["X-Frame-Options"] == "DENY"

        with urlopen(f"{base_url}/api/health", timeout=2) as response:
            health = json.load(response)
            assert health["scope"] == "localhost"
            assert health["download_ready"] is True

        with urlopen(f"{base_url}/api/jobs", timeout=2) as response:
            assert json.load(response)["counts"]["queued"] == 0


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


def test_rejects_download_when_local_setup_is_incomplete() -> None:
    health = {
        **READY_HEALTH,
        "status": "setup-required",
        "download_ready": False,
        "checks": [{"name": "FFmpeg", "ok": False, "detail": "Not found"}],
    }
    payload = json.dumps(
        {
            "url": "https://www.youtube.com/playlist?list=PL123",
            "output": "downloads",
            "dry_run": False,
            "confirm_rights": True,
        }
    ).encode()

    with running_server(health) as base_url:
        request = Request(
            f"{base_url}/api/jobs",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Origin": base_url},
        )
        try:
            urlopen(request, timeout=2)
        except HTTPError as error:
            assert error.code == 503
            assert "FFmpeg" in json.load(error)["error"]
        else:
            raise AssertionError("A download should require FFmpeg")


def test_deletes_a_queued_job() -> None:
    with running_server() as base_url:
        request = Request(f"{base_url}/api/jobs/queued", method="DELETE")
        request.add_header("Content-Type", "application/json")
        request.add_header("Origin", base_url)
        with urlopen(request, timeout=2) as response:
            result = json.load(response)
            assert response.status == 200
            assert result["state"] == "cancelled"


def test_rejects_cross_origin_cancellation() -> None:
    with running_server() as base_url:
        request = Request(
            f"{base_url}/api/jobs/queued",
            data=b"{}",
            method="DELETE",
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
            raise AssertionError("Cross-origin cancellation should be rejected")


def test_delete_unknown_job_returns_404() -> None:
    with running_server() as base_url:
        request = Request(f"{base_url}/api/jobs/missing", method="DELETE")
        request.add_header("Content-Type", "application/json")
        request.add_header("Origin", base_url)
        try:
            urlopen(request, timeout=2)
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("Unknown job should return 404")


def test_delete_non_cancellable_job_returns_409() -> None:
    with running_server() as base_url:
        request = Request(f"{base_url}/api/jobs/known", method="DELETE")
        request.add_header("Content-Type", "application/json")
        request.add_header("Origin", base_url)
        try:
            urlopen(request, timeout=2)
        except HTTPError as error:
            assert error.code == 409
        else:
            raise AssertionError("A completed job should not be cancellable")


def test_retries_a_failed_job() -> None:
    with running_server() as base_url:
        request = Request(
            f"{base_url}/api/jobs/known/retry",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json", "Origin": base_url},
        )
        with urlopen(request, timeout=2) as response:
            result = json.load(response)
            assert response.status == 202
            assert result["id"] == "retried-job"


def test_exports_job_history_as_a_download() -> None:
    with running_server() as base_url:
        response = urlopen(f"{base_url}/api/jobs/export", timeout=2)
        with response:
            assert response.status == 200
            disposition = response.headers["Content-Disposition"]
            assert disposition == 'attachment; filename="job-history.json"'
            body = json.load(response)
            assert body["counts"] == {"running": 0, "queued": 0}
