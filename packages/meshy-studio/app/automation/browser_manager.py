from __future__ import annotations

from pathlib import Path

from app.paths import app_root
import subprocess
import threading
import time


class BrowserManager:
    def __init__(self, profiles_root: str | Path):
        self.profiles_root = Path(profiles_root).resolve()
        self.profiles_root.mkdir(parents=True, exist_ok=True)
        self._playwrights: dict[int, object] = {}
        self._chrome_procs: dict[int, subprocess.Popen] = {}

    def _playwright_for_thread(self):
        """One Playwright driver per thread: a second sync_playwright().start() in the
        same thread raises 'Sync API inside the asyncio loop', which broke account rotation."""
        from playwright.sync_api import sync_playwright
        key = threading.get_ident()
        if key not in self._playwrights:
            self._playwrights[key] = sync_playwright().start()
        return self._playwrights[key]

    def profile_path(self, account_id: int) -> Path:
        if account_id <= 0:
            raise ValueError("account_id must be positive")
        path = (self.profiles_root / f"account_{account_id:06d}").resolve()
        if path.parent != self.profiles_root:
            raise ValueError("Profile path escaped root")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def launch(self, account_id: int, *, headless: bool = False, url: str = "https://www.meshy.ai/vi/workspace?sidebar=image"):
        """Launch one persistent Chromium context. Caller owns and closes the context."""
        profile = self.profile_path(account_id)
        playwright = self._playwright_for_thread()
        launch_options = {
            "headless": headless,
            "args": ["--no-first-run", "--no-default-browser-check", "--disable-sync", "--disable-session-crashed-bubble"],
        }
        extension_dir = app_root() / "docs" / "vendor" / "meshy-ai-to-stl" / "chrome-extension"
        if (extension_dir / "manifest.json").exists() and (extension_dir / "vendor" / "mesh_loader.wasm").exists():
            launch_options["args"] += [
                f"--disable-extensions-except={extension_dir}",
                f"--load-extension={extension_dir}",
            ]
        bundled = Path.home() / "AppData" / "Local" / "ms-playwright" / "chromium-1248" / "chrome-win64" / "chrome.exe"
        system_chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        # Prefer the installed Chrome: the Playwright-downloaded Chromium on this
        # machine has a broken side-by-side runtime and exits before a page opens.
        executable = system_chrome if system_chrome.exists() else bundled
        if executable.exists():
            launch_options["executable_path"] = str(executable)
        extension_dir = app_root() / "docs" / "vendor" / "meshy-ai-to-stl" / "chrome-extension"
        if (extension_dir / "manifest.json").exists() and (extension_dir / "vendor" / "mesh_loader.wasm").exists() and executable.exists():
            # System Chrome suppresses unpacked extensions when launched by
            # Playwright directly. Start Chrome with CDP, then attach Playwright;
            # this keeps the extension service worker alive in the app profile.
            port = 9222 + account_id
            cmd = [str(executable), f"--remote-debugging-port={port}", f"--user-data-dir={profile}",
                   f"--disable-extensions-except={extension_dir}", f"--load-extension={extension_dir}", url]
            self._chrome_procs[account_id] = subprocess.Popen(cmd, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            deadline = time.time() + 15
            browser = None
            while time.time() < deadline:
                try:
                    browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    break
                except Exception:
                    time.sleep(0.25)
            if browser is None:
                raise RuntimeError("Chrome CDP endpoint did not start")
            context = browser.contexts[0]
        else:
            context = playwright.chromium.launch_persistent_context(str(profile), **launch_options)
        pages = list(context.pages)
        page = next((p for p in pages if "meshy.ai" in p.url), None)
        if page is None:
            page = pages[0] if pages else context.new_page()
        # A prior interrupted run can leave unrelated restored tabs in the
        # persistent profile; keep the embedded app deterministic.
        for extra in pages:
            if extra is not page:
                try:
                    extra.close()
                except Exception:
                    pass
        page.goto(url, wait_until="domcontentloaded")
        return playwright, context

    def open_manual_login(self, account_id: int, url: str = "https://www.meshy.ai/vi/workspace?sidebar=image"):
        return self.launch(account_id, headless=False, url=url)


    def close_account(self, account_id: int, context: object | None = None) -> None:
        """Close the account's browser completely (Playwright context + every Chrome process on its profile)."""
        try:
            if context is not None:
                context.close()
        except Exception:
            pass
        proc = self._chrome_procs.pop(account_id, None)
        if proc is not None and proc.poll() is None:
            proc.terminate()
        _kill_profile_chrome(self.profile_path(account_id))


def _kill_profile_chrome(profile: Path) -> None:
    """Chrome hands a second launch over to the running instance, so kill by profile path, not by pid."""
    import os
    if os.name != "nt":
        return
    script = (
        "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | "
        f"Where-Object {{ $_.CommandLine -like '*{str(profile)}*' }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script], timeout=20,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), capture_output=True)
    except Exception:
        pass
