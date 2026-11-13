@echo off
title YouTube Playlist Download
echo ============================================
echo   YouTube Playlist Download - Local Web UI
echo ============================================
echo.

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Starting with uv...
    uv run youtube-playlist-download ui
    goto :end
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Starting with Python...
    python -m playlist_audio.cli ui
    goto :end
)

echo [ERROR] Neither 'uv' nor 'python' was found on PATH.
echo Please install Python 3.11+ from https://www.python.org or uv from https://docs.astral.sh/uv
echo.
pause

:end
