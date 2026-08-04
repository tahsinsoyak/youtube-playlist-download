"""Select a supported JavaScript runtime for modern YouTube extraction."""

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JavaScriptRuntime:
    """A locally available runtime accepted by yt-dlp."""

    name: str
    version_text: str


RUNTIME_REQUIREMENTS = (
    ("deno", (2, 3, 0)),
    ("node", (22, 0, 0)),
)


def _version_tuple(text: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)+", text)
    return tuple(int(part) for part in match.group().split(".")) if match else ()


def _meets_minimum(version: tuple[int, ...], minimum: tuple[int, ...]) -> bool:
    """Compare version tuples of unequal length, e.g. (2, 3) against (2, 3, 0)."""
    length = max(len(version), len(minimum))
    padded_version = version + (0,) * (length - len(version))
    padded_minimum = minimum + (0,) * (length - len(minimum))
    return padded_version >= padded_minimum


def find_javascript_runtime() -> JavaScriptRuntime | None:
    """Prefer Deno, then accept a sufficiently recent Node.js installation."""
    for name, minimum in RUNTIME_REQUIREMENTS:
        executable = shutil.which(name)
        if not executable:
            continue
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
        first_line = (result.stdout or result.stderr).splitlines()
        version_text = first_line[0] if first_line else ""
        if result.returncode == 0 and _meets_minimum(_version_tuple(version_text), minimum):
            return JavaScriptRuntime(name=name, version_text=version_text)
    return None


def js_runtime_options() -> dict[str, dict[str, str]]:
    """Return the yt-dlp API shape, or no enabled runtime when unavailable."""
    runtime = find_javascript_runtime()
    return {runtime.name: {}} if runtime else {}
