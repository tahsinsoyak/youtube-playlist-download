# Security policy

## Sensitive data

This project does not ask for a Google password, cookie file, or API key. Never
share those values in an issue, pull request, screenshot, or error log.

The web interface is designed to run only on `127.0.0.1`. Exposing it through a
reverse proxy, port forwarding, or a source modification is not supported.

Treat private playlist URLs and video identifiers as sensitive. Replace them
with `[REDACTED]` before reporting a problem.

## Reporting a vulnerability

Use GitHub private vulnerability reporting / Security Advisories instead of a
public issue. Include the affected version, reproduction steps, and potential
impact.

## Supported version

While the project is in the `0.x` stage, only the latest commit is supported.
Keep dependencies current because `yt-dlp` behavior can change with upstream
site changes.
