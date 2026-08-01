# Audio quality

## What does “highest-quality MP3” mean?

YouTube usually serves audio as a lossy AAC or Opus stream rather than MP3. This
project:

1. Selects the best available stream with `bestaudio/best`.
2. Converts it to MP3 with FFmpeg and LAME.
3. Uses `--audio-quality 0` by default.

`0` is the highest setting on FFmpeg's MP3 VBR scale. Re-encoding a lossy source
at a high bitrate cannot restore detail already lost by the source. The result
is a broadly compatible MP3, not archival lossless audio.

## Quality and file size

| Value | Approximate mode | Use case |
|---:|---|---|
| `0` | Best VBR | Default; prioritize quality |
| `2` | High VBR | Smaller files |
| `5` | Medium VBR | Prioritize storage space |
| `10` | Lowest VBR | Not recommended |

Example:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --audio-quality 2 `
  --confirm-rights
```

## Metadata and cover art

Available metadata such as the video title and uploader, plus the thumbnail, is
embedded in the MP3 by default. Some YouTube titles do not follow an actual
`Artist - Track` structure, so artist fields may not be perfect for every item.

Disable cover art or metadata:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --no-thumbnail `
  --no-metadata `
  --confirm-rights
```

Source: [yt-dlp post-processing options](https://github.com/yt-dlp/yt-dlp#post-processing-options)
