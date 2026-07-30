"""Local dependency checks that never contact YouTube."""

import shutil
import subprocess
import sys
from dataclasses import dataclass

from yt_dlp.version import __version__ as yt_dlp_version

from playlist_audio.runtime import find_javascript_runtime


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
        return False, "Bulunamadı"

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
                else "Deno 2.3+ veya Node.js 22+ bulunamadı"
            ),
        ),
        Check("FFmpeg", ffmpeg_ok, ffmpeg_detail),
        Check("ffprobe", ffprobe_ok, ffprobe_detail),
    ]
