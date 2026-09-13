"""Playwright smoke test for the local web interface."""

import json
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://127.0.0.1:8765"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "test-results"
PUBLIC_ASSETS_DIR = Path(__file__).resolve().parents[1] / "docs" / "assets"


def run() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    PUBLIC_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []
    pending_requests: set[str] = set()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        health_page = browser.new_page()
        health_response = health_page.goto(f"{BASE_URL}/api/health")
        assert health_response is not None and health_response.status == 200
        health_page.close()

        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("request", lambda request: pending_requests.add(request.url))
        page.on("requestfinished", lambda request: pending_requests.discard(request.url))
        page.on("requestfailed", lambda request: pending_requests.discard(request.url))

        page.goto(BASE_URL)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            raise AssertionError(
                f"Network did not become idle: {sorted(pending_requests)}"
            ) from None
        expect(page).to_have_title("YouTube Playlist Download — Local UI + CLI")
        expect(page.get_by_role("heading", name="Bring your playlist home.")).to_be_visible()
        expect(page.get_by_role("heading", name="Interface or terminal.")).to_be_visible()
        expect(page.locator(".access-card code")).to_have_count(2)
        expect(page.locator("#health-badge")).to_contain_text(
            re.compile(r"Local device only|Preview ready"),
        )

        profile = page.locator("#browser-profile")
        expect(profile).to_be_disabled()
        page.locator("#browser").select_option("firefox")
        expect(profile).to_be_enabled()
        expect(page.locator("#browser-hint")).to_contain_text("Firefox")
        page.locator("#browser").select_option("chrome")
        expect(page.locator("#browser-hint")).to_contain_text("interface is open in Chrome")
        page.locator("#browser").select_option("")
        expect(profile).to_be_disabled()

        dry_run = page.locator("#dry-run")
        mode_toggle = page.locator(".toggle")
        button_label = page.locator("#button-label")
        expect(button_label).to_have_text("Start safe preview")
        mode_toggle.click()
        expect(dry_run).not_to_be_checked()
        expect(button_label).to_have_text("Start MP3 download")
        page.locator("details summary").click()
        page.locator("#format").select_option("opus")
        expect(button_label).to_have_text("Start OPUS download")
        page.locator("#format").select_option("mp3")
        page.locator("details summary").click()
        mode_toggle.click()
        expect(dry_run).to_be_checked()

        page.locator("#url").fill("https://www.youtube.com/watch?v=YE7VzlLtp-4")
        page.locator("#confirm-rights").check()
        page.locator("#submit-button").click()
        expect(page.locator("#job-state")).to_have_text(
            re.compile(r"^(COMPLETE|ERROR)$"),
            timeout=90_000,
        )
        if page.locator("#job-state").text_content() == "ERROR":
            raise AssertionError(page.locator("#job-message").text_content())
        expect(page.locator("#job-message")).to_have_text("Preview complete")
        expect(page.locator("#url")).to_have_value("https://www.youtube.com/watch?v=YE7VzlLtp-4")
        expect(dry_run).not_to_be_checked()
        expect(button_label).to_have_text("Access confirmed — download MP3")
        page.screenshot(path=RESULTS_DIR / "ui-desktop.png", full_page=True)

        queue_snapshot = {
            "active": {
                "id": "active-job",
                "sequence": 2,
                "state": "running",
                "progress": 42.5,
                "message": "Downloading audio stream",
                "current_item": "Night Drive — Demo Track 03",
                "playlist_title": "Weekend Archive",
                "downloaded_bytes": 512_000,
                "total_bytes": 1_000_000,
                "speed": 256_000,
                "eta": 75,
                "item_index": 3,
                "item_count": 10,
                "queue_position": None,
                "dry_run": False,
                "audio_format": "opus",
                "output": "Music Library",
            },
            "queued": [
                {
                    "id": "queued-job",
                    "sequence": 3,
                    "state": "queued",
                    "queue_position": 1,
                    "dry_run": False,
                    "audio_format": "opus",
                    "output": "Music Library",
                }
            ],
            "recent": [],
            "counts": {"running": 1, "queued": 1},
        }
        ready_health = {
            "status": "ok",
            "scope": "localhost",
            "preview_ready": True,
            "download_ready": True,
            "checks": [],
        }
        queue_page = browser.new_page(viewport={"width": 1440, "height": 1100})
        queue_page.route(
            "**/api/health",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(ready_health),
            ),
        )
        queue_page.route(
            "**/api/jobs",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(queue_snapshot),
            ),
        )
        queue_page.goto(BASE_URL)
        queue_page.wait_for_load_state("networkidle")
        expect(queue_page.locator("#job-state")).to_have_text("RECORDING")
        expect(queue_page.locator("#job-percent")).to_have_text("%43")
        expect(queue_page.locator("#metric-track")).to_have_text("3 / 10")
        expect(queue_page.locator("#metric-speed")).to_have_text("250 KB/s")
        expect(queue_page.locator("#metric-eta")).to_have_text("1 min 15 sec")
        expect(queue_page.locator("#queue-count")).to_have_text("1 waiting")
        expect(queue_page.locator("#queue-list li")).to_have_count(1)
        expect(queue_page.locator("#queue-list li small")).to_contain_text("OPUS")
        expect(queue_page.locator("#cancel-active-button")).to_be_visible()
        expect(queue_page.locator("#submit-button")).to_be_enabled()
        expect(queue_page.locator("#button-label")).to_have_text("Queue preview")
        queue_page.screenshot(path=RESULTS_DIR / "ui-queue.png", full_page=True)
        queue_page.screenshot(path=PUBLIC_ASSETS_DIR / "ui-desktop.png", full_page=True)
        queue_page.locator(".deck").screenshot(path=PUBLIC_ASSETS_DIR / "ui-queue.png")
        queue_page.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.route(
            "**/api/health",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(ready_health),
            ),
        )
        mobile.route(
            "**/api/jobs",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(queue_snapshot),
            ),
        )
        mobile.goto(BASE_URL)
        mobile.wait_for_load_state("networkidle")
        expect(mobile.get_by_role("heading", name="Bring your playlist home.")).to_be_visible()
        mobile.screenshot(path=RESULTS_DIR / "ui-mobile.png", full_page=True)
        mobile.screenshot(path=PUBLIC_ASSETS_DIR / "ui-mobile.png", full_page=True)
        has_overflow = mobile.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        overflow_elements = mobile.evaluate(
            """[...document.querySelectorAll('*')]
              .filter((element) => element.getBoundingClientRect().right > window.innerWidth)
              .map((element) => `${element.tagName}.${element.className}`)
              .slice(0, 10)"""
        )
        assert not has_overflow, f"Mobile layout overflow: {overflow_elements}"

        browser.close()

    if console_errors:
        raise AssertionError(f"Browser console errors: {console_errors}")
    print("UI smoke test passed: desktop, mobile, form validation, no console errors")


if __name__ == "__main__":
    run()
