# Contributing

Keep contributions small, single-purpose, and covered by tests.

## Local checks

```powershell
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=playlist_audio
uv run playwright install chromium
```

## Scope and safety

- Do not remove the download-authorization model or `--confirm-rights` check.
- Never log passwords, cookie contents, or session tokens.
- Do not add DRM or access-control bypass features.
- Network-dependent tests must not be part of the default test suite.
- Keep source and Markdown files focused and below 500 lines.

Always redact private playlist URLs, cookie files, and personal account details
from bug reports.
