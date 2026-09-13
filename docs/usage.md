# Usage guide

## Commands

### Local web interface

```powershell
uv run youtube-playlist-download ui
```

This is the recommended option for everyday use. The browser opens
automatically, and the form exposes the most important CLI options. See
[Local web interface](web-ui.md) for details.

### System diagnostics

```powershell
uv run youtube-playlist-download doctor
```

Checks Python, `yt-dlp`, FFmpeg, and `ffprobe`. This command does not connect to
YouTube.

### Download

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" --confirm-rights
```

Core options:

| Option | Default | Description |
|---|---:|---|
| `--output`, `-o` | `downloads` | Root folder for the music library |
| `--browser` | none | Signed-in browser session for private content |
| `--browser-profile` | none | Specific browser profile |
| `--audio-quality` | `0` | FFmpeg VBR quality; `0` is best |
| `--audio-format` | `mp3` | Output codec: MP3, M4A, or Opus |
| `--playlist-items` | all | Playlist positions or ranges to download |
| `--archive` | under output | IDs of successful downloads |
| `--dry-run` | off | Check access and selection without writing media |
| `--no-thumbnail` | off | Disable embedded cover art |
| `--no-metadata` | off | Disable embedded metadata |
| `--confirm-rights` | required | Confirm permission to download |

Show every option:

```powershell
uv run youtube-playlist-download download --help
```

## Download part of a playlist

First 10 items:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --playlist-items "1:10" `
  --confirm-rights
```

Specific items:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --playlist-items "1,3,7" `
  --confirm-rights
```

## Choose another output folder

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --output "D:\Music\YouTube Archive" `
  --confirm-rights
```

## Prevent duplicate downloads

Each successful download is recorded in `.playlist-audio-archive.txt` under the
output folder by default. Recorded videos are skipped when the same playlist is
run again. The archive contains media identifiers only, never session cookies.

Use separate archive files when the same video intentionally belongs in more
than one collection:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --archive ".state\my-playlist.txt" `
  --confirm-rights
```

## Configuration file

Repeated flags can be set once in `~/.playlist-audio/config.toml` instead of
being passed on every run. A flag on the command line always takes priority
over the config file.

```toml
output = "D:/Music/YouTube Archive"
browser = "firefox"
browser_profile = "default-release"
audio_quality = "0"
audio_format = "mp3"
port = 8765
```

Recognized keys: `output`, `browser`, `browser_profile`, `audio_quality`, and
`audio_format` (used by `download`), and `port` (used by `ui`). Unknown keys are
ignored, and a missing or unreadable file is treated the same as no config at all.
