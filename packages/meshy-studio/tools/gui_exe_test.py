"""Phase D: drives the BUILT EXE through Windows UI Automation (real window, real clicks, real file dialog).

Usage: python tools/gui_exe_test.py [path-to-exe]
NO mouse, NO keyboard, NO focus change: only UI Automation patterns (Invoke / Select / Value) and PrintWindow screenshots,
so the person using the PC is never disturbed. The exe starts without activating its window. Isolated temp folder, own
data/, no network, no browser (MESHY_AUTOSTART=0). Drag & drop from Explorer is NOT driven (it needs the mouse).
"""
import ctypes
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ctypes import wintypes

from pywinauto import Desktop

REPO = Path(__file__).resolve().parents[1]
EXE_SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "MeshyAIStudio.exe"
OUT = REPO / "output" / "gui_exe"
PAGES = ["Generate", "Queue", "Accounts", "Purelymail", "Library", "Settings", "Logs"]
# one control that exists ONLY on that page: hidden pages are absent from the UI Automation tree, so this proves the page is shown
MARKERS = {"Generate": ("Drop images here.*|Queued .*", "Button"), "Queue": ("Cancel selected", "Button"),
           "Accounts": ("Use selected account", "Button"), "Purelymail": ("Add mailbox...", "Button"),
           "Library": ("Open model", "Button"), "Settings": ("Apply", "Button"), "Logs": ("Export log...", "Button")}
results: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append({"check": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
    return bool(ok)


def find_window(timeout: float = 60, exclude_handles: set[int] | None = None):
    end = time.time() + timeout
    while time.time() < end:
        found = Desktop(backend="uia").windows(title="Meshy AI Studio", visible_only=True)
        found = [window for window in found if window.handle not in (exclude_handles or set())]
        if found:
            return Desktop(backend="uia").window(handle=found[0].handle)
        time.sleep(0.5)
    return None


def launch(workdir: Path):
    existing = {window.handle for window in Desktop(backend="uia").windows(title="Meshy AI Studio", visible_only=True)}
    started = time.time()
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 4  # SW_SHOWNOACTIVATE: the window appears but never takes the focus
    proc = subprocess.Popen([str(workdir / "MeshyAIStudio.exe")], cwd=str(workdir), env=dict(os.environ, MESHY_AUTOSTART="0"),
                            startupinfo=startup)
    win = find_window(exclude_handles=existing)
    return proc, win, time.time() - started


def texts(win) -> list[str]:
    """Every visible name in the window: labels AND table cells (cells are not 'Text' controls)."""
    return [c.element_info.name for c in win.descendants() if c.element_info.name]


def wait_text(win, needle: str, timeout: float = 4.0) -> float | None:
    """Seconds until a Text control containing `needle` appears (None = it never did): also the UI-freeze check."""
    start = time.time()
    while time.time() - start < timeout:
        if any(needle in t for t in texts(win)):
            return time.time() - start
        time.sleep(0.1)
    return None


def shot(win, name: str) -> None:
    """PrintWindow capture of THIS window only (works even when other windows cover it; touches nothing else)."""
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    hwnd = win.handle
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bitmap = gdi32.CreateCompatibleBitmap(hdc, width, height)
    gdi32.SelectObject(mem, bitmap)
    user32.PrintWindow(hwnd, mem, 2)  # PW_RENDERFULLCONTENT

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]
    header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(mem, bitmap, 0, height, buffer, ctypes.byref(header), 0)
    Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1).convert("RGB").save(OUT / f"{name}.png")
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)


def press(control) -> None:
    """Activate a control through UI Automation patterns only. There is deliberately NO mouse/keyboard fallback:
    a control that cannot be driven this way is an accessibility bug of the app and fails the check."""
    wrapper = control.wrapper_object() if hasattr(control, "wrapper_object") else control
    errors = []
    kind = wrapper.element_info.control_type
    # list/table items: Invoke exists but does nothing in Qt, Select is the real action; buttons are the other way round
    for method in (("select", "invoke") if kind in ("ListItem", "DataItem") else ("invoke", "select")):
        try:
            getattr(wrapper, method)()
            return
        except Exception as error:
            errors.append(f"{method}: {type(error).__name__}")
    raise RuntimeError("control not drivable through UI Automation (" + ", ".join(errors) + ")")


def page_visible(win, page: str, timeout: float = 2.0) -> bool:
    pattern, kind = MARKERS[page]
    end = time.time() + timeout
    while time.time() < end:
        if win.child_window(title_re=pattern, control_type=kind).exists(timeout=0.2):
            return True
    return False


def click_item(win, title: str, control_type: str) -> None:
    item = win.child_window(title=title, control_type=control_type)
    press(item)


def pick_files(win, paths: list[Path]) -> bool:
    """Fills the real Windows file dialog with absolute paths and presses its Open button (no global keystrokes)."""
    dialog = None
    for _ in range(40):
        # the Qt file dialog is an OWNED window of the main window, so look among the main window's children
        owned = [c for c in win.children() if c.window_text() == "Choose input images" and c.class_name() == "#32770"]
        if owned:
            dialog = Desktop(backend="uia").window(handle=owned[0].handle)
            break
        time.sleep(0.25)
    if dialog is None:
        return False
    box = dialog.child_window(auto_id="1148", control_type="Edit")  # the "File name" box
    box.set_edit_text(str(paths[0].parent))
    press(dialog.child_window(title="Open", auto_id="1", control_type="Button"))  # a folder path just navigates there
    time.sleep(1.0)
    box.set_edit_text(" ".join(f'"{p.name}"' for p in paths))  # several names relative to that folder
    press(dialog.child_window(title="Open", auto_id="1", control_type="Button"))
    return True


def job_rows(db_path: Path) -> list[tuple]:
    con = sqlite3.connect(db_path)
    try:
        return con.execute("SELECT id, status, image_path FROM jobs ORDER BY id").fetchall()
    finally:
        con.close()


def main() -> int:
    if not EXE_SRC.is_file():
        print(f"exe not found: {EXE_SRC}")
        return 2
    workdir = Path(tempfile.mkdtemp(prefix="meshy-gui-"))
    shutil.copy(EXE_SRC, workdir / "MeshyAIStudio.exe")
    images = workdir / "images"
    images.mkdir()
    pngs = []
    for index, name in enumerate(("gate", "vase", "crystal")):
        path = images / f"{name}.png"
        from PIL import Image
        Image.new("RGB", (160, 120), (60 * index + 40, 120, 220)).save(path)
        pngs.append(path)

    proc, win, startup = launch(workdir)
    try:
        if not check("exe window opens", win is not None, f"{startup:.1f}s"):
            return 1
        check("startup under 30 s", startup < 30, f"{startup:.1f}s")
        shot(win, "01_generate")

        # --- all 7 pages --------------------------------------------------------------------------------------------
        for number, page in enumerate(PAGES, start=1):
            click_item(win, page, "ListItem")
            began = time.time()
            check(f"page '{page}' opens (its own controls are visible)", page_visible(win, page, 3), f"{time.time() - began:.2f}s")
            time.sleep(0.4)
            shot(win, f"02_page_{number}_{page.lower()}")

        # --- add jobs through the real file dialog -------------------------------------------------------------------
        click_item(win, "Generate", "ListItem")
        time.sleep(0.5)
        drop = win.child_window(title_re="Drop images here.*", control_type="Button")
        press(drop)
        check("file picker opens", pick_files(win, pngs))
        check("export folder untouched by the picker", not (workdir / "data" / "settings.json").exists())
        queued = wait_text(win, "Job 3 queued", 8)
        check("jobs are queued right after choosing files", queued is not None)
        time.sleep(1)
        shot(win, "03_after_picker")
        rows = job_rows(workdir / "data" / "meshy.sqlite3")
        check("3 jobs saved in SQLite", len(rows) == 3, str([r[1] for r in rows]))

        # --- queue page: thumbnails, pause / resume / cancel --------------------------------------------------------
        click_item(win, "Queue", "ListItem")
        time.sleep(1.2)
        shot(win, "04_queue")
        names = " ".join(texts(win))
        check("queue lists the image names", all(n in names for n in ("gate.png", "vase.png", "crystal.png")))
        check("queue shows positions", "Queued #1" in names and "Queued #3" in names)
        cells = [c for c in win.descendants() if c.element_info.name == "gate.png"]
        if cells:
            press(cells[0])
        press(win.child_window(title="Pause selected", control_type="Button"))
        check("Pause selected works", wait_text(win, "Paused 1") is not None)
        press(win.child_window(title="Resume selected", control_type="Button"))
        check("Resume selected works", wait_text(win, "Resumed 1") is not None)
        vase = [c for c in win.descendants() if c.element_info.name == "vase.png"]
        if vase:
            press(vase[0])
        press(win.child_window(title="Cancel selected", control_type="Button"))
        cancel_status = wait_text(win, "Canceled 1")
        cancel_rows = {Path(r[2]).stem: r[1] for r in job_rows(workdir / "data" / "meshy.sqlite3")}
        check("Cancel selected works", cancel_status is not None or cancel_rows.get("vase") == "Canceled",
              "status label observed" if cancel_status is not None else "persisted SQLite state observed")
        time.sleep(0.5)
        shot(win, "05_after_cancel")
        states = {Path(r[2]).stem: r[1] for r in job_rows(workdir / "data" / "meshy.sqlite3")}
        check("vase is Canceled, the others still queued", states.get("vase") == "Canceled" and states.get("gate") == "Pending"
              and states.get("crystal") == "Pending", str(states))

        # --- emergency stop -----------------------------------------------------------------------------------------
        press(win.child_window(title="EMERGENCY STOP", control_type="Button"))
        check("Emergency Stop reacts", wait_text(win, "EMERGENCY STOP: nothing new is sent") is not None)
        time.sleep(0.6)
        shot(win, "06_emergency_stop")
        states = {Path(r[2]).stem: r[1] for r in job_rows(workdir / "data" / "meshy.sqlite3")}
        check("queue paused by Emergency Stop", states.get("gate") == "Paused" and states.get("crystal") == "Paused", str(states))
        press(win.child_window(title="Resume queue", control_type="Button"))
        check("Resume queue reacts", wait_text(win, "Queue resumed") is not None)

        # --- settings page content ----------------------------------------------------------------------------------
        click_item(win, "Settings", "ListItem")
        time.sleep(0.8)
        check("settings shows the environment checks", any("Browser:" in t for t in texts(win)) and any("Blender" in t for t in texts(win)))

        # --- close and reopen: data survives -------------------------------------------------------------------------
        press(win.child_window(title="Close", control_type="Button"))
        gone = False
        for _ in range(40):
            if not Desktop(backend="uia").windows(title="Meshy AI Studio", visible_only=True):
                gone = True
                break
            time.sleep(0.25)
        check("window closes cleanly", gone)
        time.sleep(1.5)
        proc, win, startup2 = launch(workdir)
        check("exe reopens", win is not None, f"{startup2:.1f}s")
        click_item(win, "Queue", "ListItem")
        time.sleep(1.5)
        shot(win, "07_after_reopen")
        names = " ".join(texts(win))
        check("jobs are still listed after reopening", "gate.png" in names and "crystal.png" in names and "vase.png" in names)
        rows = job_rows(workdir / "data" / "meshy.sqlite3")
        check("no job lost or duplicated by the restart", len(rows) == 3, str([r[1] for r in rows]))
    finally:
        subprocess.run(["taskkill", "/IM", "MeshyAIStudio.exe", "/F"], capture_output=True)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed -> {OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
