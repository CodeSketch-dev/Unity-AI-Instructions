from pathlib import Path
import time
from playwright.sync_api import sync_playwright

PROFILE = Path('profiles/account_000001').resolve()
IMAGE = Path(r'C:\Users\Code Sketch\AppData\Local\Temp\codex-clipboard-69019928-7e0e-4629-87f2-641c1630f492.png')
OUT = Path('docs/reports/auto_probe'); OUT.mkdir(parents=True, exist_ok=True)

def vis(loc):
    try: return loc.count() > 0 and loc.first.is_visible()
    except Exception: return False

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(str(PROFILE), channel='chrome', headless=False,
        args=['--no-first-run','--no-default-browser-check','--disable-sync'])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto('https://www.meshy.ai/vi/workspace?sidebar=image', wait_until='domcontentloaded', timeout=90000)
    for i in range(80):
        page.screenshot(path=str(OUT/f'step_{i:03d}.png'), full_page=False)
        dialogs = page.locator('[role=dialog]:visible')
        text = page.locator('body').inner_text(timeout=5000)
        print('STEP', i, 'DIALOGS', dialogs.count(), 'MODEL', 'Mô hình' in text, '3D', 'Hình ảnh thành 3D' in text, flush=True)
        # subscription and generic close controls
        for name in ('Có lẽ sau','Đóng'):
            loc = page.get_by_text(name, exact=True)
            if vis(loc):
                try: loc.first.click(force=True, timeout=1500); print('CLICK', name, flush=True); page.wait_for_timeout(700)
                except Exception: pass
        # survey choices, using text fallback because some are toggle buttons
        clicked = False
        for name in ('Một mình','Tôi tự','Thành viên nhóm','Hình ảnh sản phẩm','In 3D','Trò chơi & XR','Sửa chữa AI','In Đa Màu','Google'):
            loc = page.get_by_text(name, exact=True)
            if vis(loc):
                try: loc.first.click(force=True, timeout=1200); print('CHOICE', name, flush=True); clicked=True; break
                except Exception: pass
        for name in ('Tiếp tục','Hoàn thành'):
            loc = page.get_by_role('button', name=name, exact=True)
            if vis(loc):
                try: loc.first.click(force=True, timeout=1500); print('CLICK', name, flush=True); page.wait_for_timeout(1200)
                except Exception: pass
        if dialogs.count() == 0:
            break
        page.wait_for_timeout(800)
    page.screenshot(path=str(OUT/'after_onboarding.png'), full_page=False)
    # Open model tab
    for _ in range(20):
        try: page.get_by_role('radio', name='Mô hình', exact=True).click(timeout=1000, no_wait_after=True)
        except Exception:
            try: page.get_by_text('Mô hình', exact=True).locator('xpath=..').click(timeout=1000, no_wait_after=True)
            except Exception:
                try: page.get_by_text('Mô hình', exact=True).evaluate("e=>e.parentElement.click()")
                except Exception: pass
        page.wait_for_timeout(800)
        if vis(page.get_by_role('tab', name='Hình ảnh thành 3D', exact=True)): break
    print('TAB3D', vis(page.get_by_role('tab', name='Hình ảnh thành 3D', exact=True)), flush=True)
    page.screenshot(path=str(OUT/'model_tab.png'), full_page=False)
    if not IMAGE.exists(): raise RuntimeError('image missing')
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_text('Nhấp / Kéo & Thả / Dán Hình ảnh', exact=False).click(timeout=3000)
        fc.value.set_files(str(IMAGE)); print('UPLOADED', flush=True)
    except Exception as e:
        print('UPLOAD_ERR', type(e).__name__, str(e), flush=True)
        inp = page.locator('input[type=file]')
        print('INPUTS', inp.count(), flush=True)
        if inp.count(): inp.first.set_input_files(str(IMAGE)); print('UPLOADED_INPUT', flush=True)
    page.wait_for_timeout(2500); page.screenshot(path=str(OUT/'after_upload.png'), full_page=False)
    gen = page.get_by_role('button', name='Tạo ra', exact=True)
    print('GENERATE_COUNT', gen.count(), 'ENABLED', (gen.is_enabled() if gen.count() else False), flush=True)
    if gen.count() and gen.is_enabled():
        gen.click(); print('GENERATE_CLICKED', flush=True)
        for j in range(180):
            page.wait_for_timeout(5000)
            body = page.locator('body').inner_text(timeout=5000)
            if j % 6 == 0: page.screenshot(path=str(OUT/f'gen_{j:03d}.png'), full_page=False); print('POLL',j,body[-500:].replace('\n',' | '),flush=True)
            if any(x in body.lower() for x in ('tải xuống','download','đã hoàn thành','completed','failed','thất bại')):
                print('TERMINAL_TEXT', body[-1000:], flush=True); break
    else: print('GENERATE_NOT_READY', flush=True)
    print('KEEPING_BROWSER_OPEN', flush=True)
    while True: time.sleep(10)
