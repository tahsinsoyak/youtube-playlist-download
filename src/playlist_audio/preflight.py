"""Local dependency checks that never contact YouTube."""

import shutil
import subprocess
import sys
from dataclasses import dataclass

from yt_dlp.version import __version__ as yt_dlp_version

from playlist_audio.runtime import find_javascript_runtime

PREVIEW_COMPONENTS = ("Python", "yt-dlp", "JavaScript")
DOWNLOAD_COMPONENTS = PREVIEW_COMPONENTS + ("FFmpeg", "ffprobe")


@dataclass(frozen=True, slots=True)
class Check:
    """One diagnostic check rendered by the CLI."""

    name: str
    ok: bool
    detail: str
    required: bool = True


def _command_version(command: str) -> tuple[bool, str]:
    executable = shutil.which(command)
    if executable is None:
        return False, "Not found"

    result = subprocess.run(
        [executable, "-version"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    first_line = (result.stdout or result.stderr).splitlines()
    detail = first_line[0] if first_line else executable
    return result.returncode == 0, detail


def run_checks() -> list[Check]:
    """Return Python, yt-dlp, JavaScript runtime and FFmpeg readiness."""
    ffmpeg_ok, ffmpeg_detail = _command_version("ffmpeg")
    ffprobe_ok, ffprobe_detail = _command_version("ffprobe")
    python_ok = sys.version_info >= (3, 11)
    js_runtime = find_javascript_runtime()

    return [
        Check("Python", python_ok, sys.version.split()[0]),
        Check("yt-dlp", True, yt_dlp_version),
        Check(
            "JavaScript",
            js_runtime is not None,
            (
                f"{js_runtime.name}: {js_runtime.version_text}"
                if js_runtime
                else "Deno 2.3+ or Node.js 22+ was not found"
            ),
        ),
        Check("FFmpeg", ffmpeg_ok, ffmpeg_detail),
        Check("ffprobe", ffprobe_ok, ffprobe_detail),
    ]


def readiness_status(checks: list[Check] | None = None) -> dict[str, object]:
    """Return UI-safe readiness details for previews and real downloads."""
    resolved_checks = checks if checks is not None else run_checks()
    by_name = {check.name: check for check in resolved_checks}

    def ready(required: tuple[str, ...]) -> bool:
        return all(by_name.get(name) is not None and by_name[name].ok for name in required)

    preview_ready = ready(PREVIEW_COMPONENTS)
    download_ready = ready(DOWNLOAD_COMPONENTS)
    return {
        "status": "ok" if download_ready else "setup-required",
        "scope": "localhost",
        "preview_ready": preview_ready,
        "download_ready": download_ready,
        "checks": [
            {"name": check.name, "ok": check.ok, "detail": check.detail}
            for check in resolved_checks
        ],
    }


def readiness_error(
    *,
    dry_run: bool,
    status: dict[str, object] | None = None,
) -> str | None:
    """Explain which local dependencies prevent the requested operation."""
    resolved_status = status if status is not None else readiness_status()
    required = PREVIEW_COMPONENTS if dry_run else DOWNLOAD_COMPONENTS
    raw_checks = resolved_status.get("checks", [])
    checks = {
        str(check["name"]): check
        for check in raw_checks
        if isinstance(check, dict) and "name" in check
    }
    missing = [name for name in required if name not in checks or checks[name].get("ok") is False]
    if not missing:
        return None
    operation = "preview" if dry_run else "download"
    return (
        f"Cannot start the {operation}; missing or unsupported: {', '.join(missing)}. "
        "Run 'youtube-playlist-download doctor' for setup details."
    )
