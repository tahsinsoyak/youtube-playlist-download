# Local web interface

## Start the UI

```powershell
uv run youtube-playlist-download ui
```

The default browser opens at `http://127.0.0.1:8765`. Visit that address
manually if it does not open.

Use another port:

```powershell
uv run youtube-playlist-download ui --port 9000
```

Start without opening a browser:

```powershell
uv run youtube-playlist-download ui --no-open
```

Press `Ctrl+C` in the terminal running the server to stop it.

## Workflow

1. Paste a YouTube playlist or video URL.
2. Leave the session source unchanged for a public playlist.
3. For an authorized private playlist, select a signed-in Firefox, Chrome, or
   other supported browser.
4. Choose the output folder.
5. Keep `Safe preview` enabled, confirm your rights, and start the job.
6. After a successful preview, the URL stays in place and preview mode turns
   off automatically.
7. Select `Access confirmed — download MP3` to start the real download.

Open `Fine controls` to change MP3 quality, playlist positions, browser profile,
cover art, and metadata options.

## Queue and live progress

You can paste another playlist and submit it while a download is active. The new
job does not interrupt the current one; it is added to the end of the queue.
Jobs run sequentially so they can safely share an output folder.

The live panel displays:

- Overall playlist progress and current track position
- Current transfer speed (`KB/s` or `MB/s`)
- Downloaded and estimated total size for the current track
- ETA reported by `yt-dlp`
- Pending job count and FIFO queue position

Each queued job (not yet started) shows a `Cancel` button. Cancelling removes it
from the queue without affecting the job currently downloading. The active job
cannot be cancelled once it has started.

If a playlist contains deleted or regionally unavailable entries, accessible
items continue processing. The result reports how many entries were available
and how many were skipped.

The queue and recent history are saved to `~/.playlist-audio/queue-state.json`
after every job change and restored the next time the server starts. Pending
jobs resume automatically; a job that was still downloading when the server
stopped is shown as interrupted instead, since a yt-dlp run in progress can't
be safely resumed. Completed MP3 files and the download archive remain on
disk regardless.

## Security boundaries

- The server is fixed to the `127.0.0.1` loopback interface.
- There is no option to publish it to a LAN or the internet.
- POST requests require the same host/origin and `application/json`.
- Only one download runs at a time; other jobs wait in the local FIFO queue.
- Job responses never expose the source URL.
- The UI accepts no password, cookie file, or API key.
- It loads no remote CDN, font, or JavaScript asset.

Do not expose this interface through a reverse proxy. Remote access would
require a redesigned cookie and authentication architecture.

## Real-browser smoke test

After installing development dependencies and Chromium:

```powershell
uv sync --extra dev
uv run playwright install chromium
uv run python scripts/ui_smoke_test.py
```

The smoke test expects the UI server on `127.0.0.1:8765`. It checks desktop and
mobile layouts, queue and speed metrics, form behavior, an end-to-end dry run,
and the browser console.
