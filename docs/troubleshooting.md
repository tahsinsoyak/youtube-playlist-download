# Troubleshooting

## Run diagnostics first

```powershell
uv run youtube-playlist-download doctor
```

## `ffmpeg not found`

Windows:

```powershell
winget install Gyan.FFmpeg
```

Restart the terminal and run `doctor` again.

## JavaScript runtime not found

Current YouTube flows require a JavaScript runtime so `yt-dlp` can solve player
challenges. Install Deno 2.3+ (recommended) or Node.js 22+. On Windows:

```powershell
winget install DenoLand.Deno
```

Restart the terminal and confirm the `JavaScript` row is ready in `doctor`.
The `yt-dlp[default]` dependency also installs the matching `yt-dlp-ejs` package.

## Private playlist not found

- Confirm the correct Google account is signed in within the browser.
- Pass the complete URL inside double quotes.
- Add `--browser firefox`.
- Close the browser completely and try again.
- Test access with `--dry-run` first.

## Browser cookie database is locked

Close every browser window and background process. If the issue continues on
Windows, sign in with Firefox and use `--browser firefox`.

When the UI is open in Chrome and Chrome is also selected as the session source,
Chrome keeps its cookie database locked. Open the UI in Edge or Firefox and
close Chrome completely, or use a signed-in Firefox profile as the source.

## `Sign in to confirm you're not a bot`

Keep `yt-dlp` and this project current:

```powershell
uv lock --upgrade-package yt-dlp
uv sync --locked
```

Then open YouTube normally in the browser and confirm the account works. Do not
attempt to automate CAPTCHA or platform-protection bypasses.

## Some videos are skipped

A playlist may contain deleted, region-blocked, or account-restricted items.
The CLI continues with accessible items and reports unavailable entries at the
end.

## A track is not downloaded again

The download archive records IDs that completed successfully. Choose another
`--archive` path if you intentionally want to rebuild a collection. Consider
backing up an existing archive before removing it.

## Sharing a bug report

Never share:

- Cookie files or browser profile files
- Google account details
- Private playlist URLs or IDs
- Personal folder paths

Replace private values with `[REDACTED]`, then include `doctor` output, the
operating-system version, and reproduction steps.
