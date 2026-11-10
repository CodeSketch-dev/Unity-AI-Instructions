from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


URL = "https://www.meshy.ai/vi/workspace?sidebar=image"
REPORT = Path(__file__).resolve().parents[1] / "docs" / "reports" / "meshy_auto_play_diagnostic.md"


def visible_role(page, role: str, name: str) -> bool:
    try:
        return page.get_by_role(role, name=name, exact=True).is_visible()
    except Exception:
        return False


def visible_text(page, text: str) -> bool:
    try:
        return page.get_by_text(text, exact=False).first.is_visible()
    except Exception:
        return False


def safe_url(value: str) -> str:
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def run() -> dict:
    result: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "profile": "fresh isolated temporary profile",
        "url": URL,
        "steps": [],
        "blocker": None,
    }
    with tempfile.TemporaryDirectory(prefix="meshy-diagnostic-") as profile_dir:
        with sync_playwright() as playwright:
            context = None
            try:
                try:
                    context = playwright.chromium.launch_persistent_context(
                        profile_dir, channel="chrome", headless=False
                    )
                except Exception as chrome_error:
                    result["steps"].append({"step": "launch_chrome_channel", "status": "failed", "detail": type(chrome_error).__name__})
                    context = playwright.chromium.launch_persistent_context(profile_dir, headless=False)
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_timeout(1_500)
                result["steps"].append({
                    "step": "workspace_loaded",
                    "status": "pass",
                    "url": page.url,
                    "title": page.title(),
                })

                login_modal = visible_role(page, "button", "Đăng nhập")
                result["steps"].append({"step": "login_modal_detected", "status": "pass" if login_modal else "not_detected"})

                google_clicked = False
                popup_pages = []
                if login_modal:
                    page.get_by_role("button", name="Đăng nhập", exact=True).click()
                    page.wait_for_timeout(300)
                    google = page.get_by_role("button", name="Tiếp tục với Google", exact=True)
                    google_visible = google.is_visible()
                    result["steps"].append({"step": "google_button_detected", "status": "pass" if google_visible else "not_detected"})
                    if google_visible:
                        try:
                            with context.expect_page(timeout=5_000) as popup_info:
                                google.click()
                            popup = popup_info.value
                            popup.wait_for_load_state("domcontentloaded", timeout=10_000)
                            popup_pages.append({"url": safe_url(popup.url), "title": popup.title()})
                            google_clicked = True
                        except PlaywrightTimeoutError:
                            google.click()
                            google_clicked = True
                        result["steps"].append({
                            "step": "google_button_click",
                            "status": "pass",
                            "popup_or_new_page": popup_pages,
                    "current_url": safe_url(page.url),
                        })
                else:
                    result["blocker"] = "Meshy did not expose the expected login button in a fresh profile."

                manual = any(visible_text(page, marker) for marker in ("CAPTCHA", "MFA", "verification", "xác minh"))
                result["steps"].append({"step": "manual_verification_classification", "status": "manual_verification" if manual else "not_present"})

                model_visible = visible_role(page, "radio", "Mô hình")
                image_to_3d_visible = visible_role(page, "tab", "Hình ảnh thành 3D")
                upload_ready = visible_text(page, "Nhấp / Kéo & Thả / Dán Hình ảnh")
                result["steps"].append({
                    "step": "model_tab_detection",
                    "status": "pass" if model_visible and image_to_3d_visible else "not_ready",
                    "model_radio": model_visible,
                    "image_to_3d_tab": image_to_3d_visible,
                    "upload_chooser_text": upload_ready,
                })
                if not google_clicked and login_modal:
                    result["blocker"] = "Google button was visible but OAuth popup/new-page was not observable in the headed context."
                elif google_clicked and not popup_pages:
                    result["blocker"] = "Google click was accepted but no popup/new page was observable; likely FedCM or popup policy."
                elif google_clicked and popup_pages:
                    result["blocker"] = "Google OAuth opened successfully, but this diagnostic does not enter credentials or complete MFA. Manual sign-in is required before Model → Image-to-3D can be exercised."
            except Exception as error:
                result["steps"].append({"step": "diagnostic_exception", "status": "failed", "detail": type(error).__name__})
                result["blocker"] = f"{type(error).__name__}: {error}"
            finally:
                if context is not None:
                    context.close()
    return result


def write_report(result: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Skills read: agent-team-protocol (bounded diagnostic/report), coding-discipline-karpathy (safe narrow scope), test-evidence-review (claim/evidence alignment)",
        "",
        "# Meshy Auto-Play Diagnostic",
        "",
        "Status: DONE_WITH_CONCERNS",
        "",
        "This run used a fresh temporary Playwright profile, did not enter credentials, did not upload a file, and did not click Generate.",
        "",
        "## Safe step log",
        "",
    ]
    for step in result["steps"]:
        lines.append(f"- `{step['step']}`: **{step['status']}** — `{json.dumps({k: v for k, v in step.items() if k not in {'step', 'status'}}, ensure_ascii=False)}`")
    lines.extend(["", f"## Blocker", "", result["blocker"] or "None observed.", "", "## Required next step", "", "Run the same headed flow from the desktop app with a user completing Google OAuth/MFA manually; only after an authenticated session is visible should Model → Image-to-3D and upload be exercised.", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    data = run()
    write_report(data)
    print(json.dumps(data, ensure_ascii=True, indent=2))
