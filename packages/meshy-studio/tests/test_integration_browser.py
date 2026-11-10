"""Integration tests against a LOCAL fake page (no Meshy account, no credits). Needs Google Chrome; skipped without it."""
import functools
import http.server
import threading
from pathlib import Path

import pytest

from app import bootstrap
from app.automation.meshy_adapter import MeshyWebAdapter as A, dismiss_onboarding

pytestmark = pytest.mark.skipif(bootstrap.chrome_path() is None, reason="Google Chrome is not installed")
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def site():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FIXTURES))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/fake_meshy.html"
    server.shutdown()


@pytest.fixture()
def page(site):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(bootstrap.chrome_path()), headless=True)
        tab = browser.new_page()
        tab.goto(site)
        yield tab
        browser.close()


def test_adapter_reads_credits_cards_and_waits_for_a_new_asset(page):
    assert A.read_credits(page) == 75
    assert A.count_cards(page) == 0
    page.get_by_test_id("workspace-generate-btn").click()
    assert A.wait_for_new_asset(page, 0, 5000) is True  # a card appeared (old cards would not count)
    assert A.wait_for_new_asset(page, 5, 500) is False  # nothing new within the window
    assert A.wait_for_cards_idle(page, 8000) is True    # the "10%" progress text disappears


def test_tour_popup_is_dismissed_and_upload_uses_the_hidden_input(page, tmp_path):
    assert page.locator("[role=dialog]").count() == 1
    dismiss_onboarding(page, 6)
    assert page.locator("[role=dialog]").count() == 0
    image = tmp_path / "a.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    A.upload_image(page, image)
    assert page.evaluate("document.getElementById('file').files.length") == 1


def test_browser_session_lifecycle_opens_and_fully_closes_the_account_browser(tmp_path, site):
    """BrowserManager: launch a real profile window, use it, then close it with no Chrome process left behind."""
    import subprocess
    from app.automation.browser_manager import BrowserManager
    manager = BrowserManager(tmp_path / "profiles")
    playwright, context = manager.launch(7, headless=False, url=site)
    try:
        assert any("fake_meshy" in p.url for p in context.pages)
    finally:
        manager.close_account(7, context)
    profile = str(manager.profile_path(7))
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          f"(Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object {{ $_.CommandLine -like '*{profile}*' }}).Count"],
                         capture_output=True, text=True).stdout.strip()
    assert out in ("", "0")
