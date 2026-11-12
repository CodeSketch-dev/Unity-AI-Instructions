from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


URL = "https://www.meshy.ai/vi/workspace?sidebar=image"
ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "live_account_14"
REPORT = ROOT / "docs" / "reports" / "meshy_live_generation.md"
SCREENSHOT = ROOT / "docs" / "reports" / "meshy_live_generation.png"
STOP_FILE = Path(os.environ.get("MESHY_STOP_FILE", str(PROFILE / "STOP")))
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\Code Sketch\AppData\Local\Temp\codex-clipboard-69019928-7e0e-4629-87f2-641c1630f492.png")


def visible_role(page, role: str, name: str) -> bool:
    try:
        return page.get_by_role(role, name=name, exact=True).is_visible()
    except Exception:
        return False


def body_text(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=1_000)
    except Exception:
        return ""


def write_report(status: str, steps: list[dict], blocker: str | None = None) -> None:
    lines = [
        "Skills read: agent-team-protocol (persistent headed handoff), test-evidence-review (live claim proof), coding-discipline-karpathy (single Generate action)",
        "",
        "# Meshy Live Generation",
        "",
        f"Status: {status}",
        "",
        f"Started: {datetime.now(timezone.utc).isoformat()}",
        f"Source image: `{SOURCE}`",
        f"Persistent profile: `{PROFILE}`",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        lines.append(f"- `{step.get('step')}`: **{step.get('status')}** — {json.dumps({k: v for k, v in step.items() if k not in {'step', 'status'}}, ensure_ascii=False)}")
    lines.extend(["", "## Blocker", "", blocker or "None", "", "## Artifacts", "", f"- Screenshot: `{SCREENSHOT}`" if SCREENSHOT.exists() else "- Screenshot: not captured", ""])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def keep_browser_open() -> None:
    while not STOP_FILE.exists():
        time.sleep(2)


def run() -> None:
    steps: list[dict] = []
    blocker = None
    PROFILE.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        write_report("BLOCKED", [{"step": "source_image", "status": "failed", "path": str(SOURCE)}], "Source image does not exist.")
        keep_browser_open()
        return

    playwright = sync_playwright().start()
    context = None
    try:
        try:
            context = playwright.chromium.launch_persistent_context(str(PROFILE), channel="chrome", headless=False)
        except Exception as error:
            steps.append({"step": "launch_chrome_channel", "status": "failed", "detail": type(error).__name__})
            context = playwright.chromium.launch_persistent_context(str(PROFILE), headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1_500)
        steps.append({"step": "workspace_loaded", "status": "pass", "url": page.url, "title": page.title()})

        if visible_role(page, "button", "Đăng nhập"):
            page.get_by_role("button", name="Đăng nhập", exact=True).click()
            page.wait_for_timeout(300)
            google = page.get_by_role("button", name="Tiếp tục với Google", exact=True)
            if not google.is_visible():
                blocker = "Login modal opened without the observed Google button."
                write_report("BLOCKED", steps, blocker)
                keep_browser_open()
                return
            try:
                with context.expect_page(timeout=5_000) as popup_info:
                    google.click()
                popup = popup_info.value
                popup.wait_for_load_state("domcontentloaded", timeout=10_000)
                steps.append({"step": "google_oauth_opened", "status": "pass", "url": popup.url.split("?", 1)[0]})
            except PlaywrightTimeoutError:
                google.click()
                steps.append({"step": "google_oauth_opened", "status": "unknown", "url": "no popup observed"})

            write_report("WAITING_FOR_MANUAL_GOOGLE", steps, "Browser is intentionally left open at Google OAuth. Complete Google sign-in/MFA manually; the runner will continue when the Meshy workspace becomes authenticated.")
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                if visible_role(page, "radio", "Mô hình") and not visible_role(page, "button", "Đăng nhập"):
                    break
                page.wait_for_timeout(1_000)
            else:
                write_report("BLOCKED", steps, "Google OAuth did not return to an authenticated Meshy workspace within 10 minutes. Browser remains open.")
                keep_browser_open()
                return

        if not visible_role(page, "radio", "Mô hình"):
            blocker = "Authenticated workspace did not expose the observed Model radio. Browser remains open."
            write_report("BLOCKED", steps, blocker)
            keep_browser_open()
            return
        page.get_by_role("radio", name="Mô hình", exact=True).click()
        page.wait_for_timeout(800)
        model_tab = page.get_by_role("tab", name="Hình ảnh thành 3D", exact=True)
        if not model_tab.is_visible():
            write_report("BLOCKED", steps, "Model radio opened no Image-to-3D tab. Browser remains open.")
            keep_browser_open()
            return
        steps.append({"step": "model_image_to_3d", "status": "pass"})

        image_input = page.locator('input[type="file"]').first
        image_input.set_input_files(str(SOURCE))
        page.wait_for_timeout(3_000)
        thumbnail_count = page.locator("img").count()
        steps.append({"step": "upload_sheet", "status": "pass" if thumbnail_count > 0 else "unknown", "image_elements": thumbnail_count})
        if thumbnail_count <= 0:
            write_report("BLOCKED", steps, "Upload did not expose a visible image element; Generate was not clicked. Browser remains open.")
            keep_browser_open()
            return

        generate = page.get_by_role("button", name="Tạo ra", exact=True)
        if not generate.is_visible() or not generate.is_enabled():
            write_report("BLOCKED", steps, "Generate button was not enabled after upload; no credit was spent. Browser remains open.")
            keep_browser_open()
            return
        generate.click()
        steps.append({"step": "generate", "status": "clicked_once"})
        write_report("GENERATING", steps)

        deadline = time.monotonic() + 1_800
        completed = False
        while time.monotonic() < deadline:
            text = body_text(page).lower()
            if re.search(r"completed|succeeded|hoàn thành|thành công", text):
                completed = True
                break
            if re.search(r"failed|error|thất bại|quota|credit", text):
                blocker = "Meshy displayed a failure, quota, or credit error in the visible UI."
                break
            page.wait_for_timeout(5_000)
        page.screenshot(path=str(SCREENSHOT), full_page=True)
        write_report("PASS" if completed else "FAILED", steps, blocker or ("Timed out while waiting for visible completion state." if not completed else None))
        keep_browser_open()
    except Exception as error:
        write_report("FAILED", steps, f"{type(error).__name__}: {error}. Browser remains open for inspection.")
        keep_browser_open()
    finally:
        # Intentionally do not close context or stop Playwright: owner requires headed browser to remain open.
        pass


if __name__ == "__main__":
    run()
