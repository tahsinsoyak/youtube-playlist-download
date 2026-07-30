"""Cross-platform terminal setup."""

import os
import sys
from typing import TextIO


def _set_utf8(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def configure_utf8_output() -> None:
    """Prevent Turkish text failures in legacy or redirected Windows shells."""
    if os.name == "nt":
        _set_utf8(sys.stdout)
        _set_utf8(sys.stderr)
