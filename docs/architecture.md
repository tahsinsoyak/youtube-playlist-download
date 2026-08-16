# Architecture and development

## Components

```text
UI input
  -> web/handler.py         Loopback HTTP and security headers
  -> web/request_parser.py  JSON validation
  -> web/jobs.py            Single-worker FIFO job queue
  -> web/job_state.py       Safe job state exposed through the API
  -> web/persistence.py     Queue and history saved to/restored from disk
  -> web/progress.py        Speed, ETA, and playlist progress calculations
  -> web/assets/            HTML, CSS, and JavaScript

CLI or validated UI request
  -> validation.py          URL and option validation
  -> models.py              Immutable request model
  -> options.py             yt-dlp option construction
  -> downloader.py          yt-dlp runtime adapter
  -> runtime.py             Deno/Node selection
  -> FFmpeg                 MP3 conversion and metadata

doctor
  -> preflight.py           Local dependency diagnostics
```

For private access, the selected browser and profile are passed to the `yt-dlp`
API. The app does not directly read, write, or log cookie contents.

## File responsibilities

- `src/playlist_audio/cli.py`: command interface and exit codes
- `src/playlist_audio/validation.py`: pure input validation
- `src/playlist_audio/options.py`: pure yt-dlp option construction
- `src/playlist_audio/downloader.py`: filesystem and yt-dlp side effects
- `src/playlist_audio/preflight.py`: local tool diagnostics
- `src/playlist_audio/runtime.py`: supported JavaScript-runtime selection
- `src/playlist_audio/web/`: localhost UI, API, job state, and static assets
- `tests/`: unit tests that do not require network access

## Development setup

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run playwright install chromium
```

## Design decisions

- Localhost-only web UI keeps session data away from remote servers.
- `yt-dlp` replaces `youtube-dl` for active maintenance, modern YouTube support,
  and browser-cookie integration.
- No cookie files reduces accidental commits and sharing.
- A download archive makes large playlist runs repeatable and duplicate-safe.
- A single-worker queue prevents output collisions while accepting new jobs.
- Explicit rights confirmation defines a responsible public-distribution boundary.
- Queue state persists to `~/.playlist-audio/queue-state.json` via a
  write-to-temp-then-rename so a crash never leaves a partially written file.
  A job that was mid-download when the app closed is restored as failed
  rather than silently resumed, since a yt-dlp run can't be resumed mid-call.

## Future improvements

- Playlist manifests and change reports
- Interactive MP3 tag correction
- Signed release packages
