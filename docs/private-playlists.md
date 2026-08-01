# Private playlist access

YouTube does not provide a reliable direct username/password login for this CLI.
The method recommended by `yt-dlp` is to read cookies from a browser where you
are already signed in.

## Recommended workflow

1. Sign in to the YouTube account that can view the playlist in Firefox.
2. Open the playlist URL in the browser and verify access.
3. Close Firefox completely.
4. Run a preview:

```powershell
uv run youtube-playlist-download download "PRIVATE_PLAYLIST_URL" `
  --browser firefox `
  --dry-run `
  --confirm-rights
```

5. Remove `--dry-run` after confirming the playlist is correct.

## Chrome or Edge

```powershell
uv run youtube-playlist-download download "PRIVATE_PLAYLIST_URL" `
  --browser chrome `
  --confirm-rights
```

On Windows, Chromium-based browsers may lock their cookie database or use
operating-system encryption that cannot be read while the browser is open.
Close every browser window and background process first. A Firefox profile is
often more reliable if the problem continues.

If the UI itself is open in Chrome, Chrome's cookies naturally remain locked.
Open the UI in Edge or Firefox, close Chrome completely, and then select Chrome
as the session source. Alternatively, sign in to YouTube in Firefox and select
Firefox in the UI.

Use a specific profile:

```powershell
uv run youtube-playlist-download download "PRIVATE_PLAYLIST_URL" `
  --browser firefox `
  --browser-profile "default-release" `
  --confirm-rights
```

Find profile paths at `about:profiles` in Firefox, `chrome://version` in Chrome,
or `edge://version` in Edge.

## Security model

- The app never asks for your Google password.
- The app does not accept or create cookie files.
- `yt-dlp` reads the required session from the selected browser profile at run
  time.
- Cookies are sent only by `yt-dlp` to YouTube for the access request.
- Review download folders and detailed error logs before sharing them.

A browser session is sensitive account-access data. Never upload a `cookies.txt`
file to a repository, issue, message, or cloud drive.

Source: [yt-dlp FAQ — cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
