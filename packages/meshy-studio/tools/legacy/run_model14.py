from pathlib import Path
import time
from playwright.sync_api import sync_playwright

PROFILE=Path('profiles/account_000001').resolve()
IMAGE=Path(r'C:\Users\Code Sketch\AppData\Local\Temp\codex-clipboard-6358e580-1fd3-4705-b6e6-3a90d89d41cf.png')
OUT=Path('Export'); OUT.mkdir(parents=True, exist_ok=True)

def visible(loc):
    try: return loc.count()>0 and loc.first.is_visible()
    except: return False

with sync_playwright() as p:
    ext=Path('docs/vendor/meshy-ai-to-stl/chrome-extension').resolve()
    ctx=p.chromium.launch_persistent_context(str(PROFILE), channel='chrome', headless=False,
      accept_downloads=True, downloads_path=str(OUT), args=['--no-first-run','--no-default-browser-check','--disable-sync',f'--disable-extensions-except={ext}',f'--load-extension={ext}'])
    pg=ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto('https://www.meshy.ai/vi/workspace?sidebar=image',wait_until='domcontentloaded',timeout=60000)
    pg.wait_for_timeout(3000)
    # Close all known blocking overlays.
    for _ in range(12):
      for n in ('Hiểu rồi','Đã hiểu','Có lẽ sau','Đóng','Bỏ qua'):
        l=pg.get_by_text(n,exact=True)
        if visible(l):
          try:l.first.click(force=True,timeout=700)
          except:pass
      if not visible(pg.locator('[role=dialog]:visible')): break
      pg.wait_for_timeout(400)
    # Model rail item is a span; click its parent.
    m=pg.get_by_text('Mô hình',exact=True)
    if visible(m): m.locator('xpath=..').click(force=True,timeout=3000,no_wait_after=True)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT/'model14_before_upload.png'))
    with pg.expect_file_chooser(timeout=8000) as fc:
      pg.get_by_text('Nhấp / Kéo & Thả / Dán Hình ảnh',exact=False).click(force=True)
    fc.value.set_files(str(IMAGE)); pg.wait_for_timeout(1500)
    # Enable Meshy's texture pass before generating (the GitHub decoder exports
    # whatever Meshy embeds in the resulting .meshy resource).
    texture = pg.get_by_text('Kết cấu', exact=True)
    if visible(texture):
      parent = texture.locator('xpath=..')
      switch = parent.get_by_role('switch')
      checkbox = parent.locator('input[type=checkbox]')
      try:
        if switch.count() and not switch.first.is_checked(): switch.first.click(force=True)
      except:
        try:
          if checkbox.count() and not checkbox.first.is_checked(): checkbox.first.check(force=True)
        except: pass
    gen=pg.get_by_role('button',name='Tạo ra',exact=True)
    print('GENERATE_READY',gen.count(),gen.is_enabled() if gen.count() else False,flush=True)
    gen.click(force=True); print('GENERATE_CLICKED',flush=True)
    start=time.time(); last=''
    while time.time()-start<900:
      pg.wait_for_timeout(5000)
      body=pg.locator('body').inner_text()
      # Print progress changes only.
      lines=[x.strip() for x in body.splitlines() if '%' in x or 'Đang tạo' in x or 'Topology' in x or 'Tải xuống' in x]
      sig=' | '.join(lines[-12:])
      if sig!=last: print('STATUS',sig,flush=True); last=sig
      low=body.lower()
      if 'đang tạo mô hình' not in low and ('topology' in low or 'mặt' in low) and ('0%' not in sig or '100%' in sig):
        break
    pg.screenshot(path=str(OUT/'model14_generated.png'))
    # Dismiss API/onboarding overlays and select the newly-created task card,
    # not a previously selected community asset.
    for n in ('Đóng', 'Hiểu rồi', 'Đã hiểu'):
      l=pg.get_by_text(n,exact=True)
      if visible(l):
        try:l.first.click(force=True,timeout=1000)
        except:pass
    generated=pg.locator('img[src*="api.meshy.ai/misc/cdn-images"]').first
    if visible(generated):
      generated.click(force=True,timeout=2000)
      pg.wait_for_timeout(800)
    # Open overflow menu, then exact remesh flow.
    # Card overflow menu (the ellipsis on the selected generated card).
    card=generated.locator('xpath=..') if visible(generated) else pg.locator('body')
    if visible(generated):
      try: generated.hover(force=True)
      except: pass
    buttons=pg.get_by_role('button')
    # Walk image ancestors; the selected card's overflow button is rendered on hover.
    for depth in range(1,9):
      try:
        candidate=generated.locator('xpath=' + '/..'*depth)
        cb=candidate.get_by_role('button')
        if cb.count():
          print('CARD_BUTTONS',depth,cb.count(),flush=True)
          cb.last.click(force=True,timeout=700)
          if visible(pg.get_by_text('Remesh',exact=True)): break
      except: pass
    buttons=pg.get_by_role('button')
    for i in range(buttons.count()):
      b=buttons.nth(i)
      try:
        label=((b.get_attribute('aria-label') or '')+' '+(b.inner_text() or '')).lower()
        if any(x in label for x in ('more','thêm','ellipsis','...')):
          b.click(force=True,timeout=700); break
      except: pass
    rem=pg.get_by_text('Remesh',exact=True)
    edit=pg.get_by_text('Chỉnh sửa mô hình',exact=True)
    if visible(edit):
      try: edit.first.hover(force=True,timeout=1000); pg.wait_for_timeout(500)
      except: pass
    rem=pg.get_by_text('Remesh',exact=True)
    if not visible(rem):
      # last small toolbar buttons often expose an unlabeled overflow button
      for i in range(max(0,buttons.count()-8),buttons.count()):
        try: buttons.nth(i).click(force=True,timeout=500); rem=pg.get_by_text('Remesh',exact=True); 
        except: pass
        if visible(rem): break
    print('REMESH_VISIBLE',visible(rem),flush=True)
    if visible(rem): rem.first.click(force=True,timeout=1500)
    fixed=pg.get_by_text('Cố định',exact=True)
    if visible(fixed): fixed.first.click(force=True,timeout=1000)
    opt=pg.get_by_text('10K',exact=True)
    print('10K_VISIBLE',visible(opt),flush=True)
    if visible(opt): opt.first.click(force=True,timeout=1000)
    tri=pg.get_by_text('Triangle',exact=True)
    if visible(tri):
      try: tri.first.click(force=True,timeout=1000)
      except: pass
    confirm=pg.get_by_role('button',name='Xác nhận',exact=True)
    if visible(confirm): confirm.first.click(force=True,timeout=1500); print('REMESH_10K_CONFIRMED',flush=True)
    pg.wait_for_timeout(5000); pg.screenshot(path=str(OUT/'model14_10k.png'))
    # Export through the installed GitHub extension, using the authenticated
    # Meshy tab's .meshy request and local decoder.
    workers=ctx.service_workers
    if not workers:
      try: ctx.wait_for_event('serviceworker', timeout=10000)
      except: pass
    workers=ctx.service_workers
    if workers:
      ext_id=workers[0].url.split('/')[2]
      export=ctx.new_page(); awaitable=export.goto(f'chrome-extension://{ext_id}/automation.html')
      export.wait_for_timeout(15000)
      print('EXTENSION_EXPORT_TITLE',export.title(),flush=True)
    print('BROWSER_OPEN',flush=True)
    while True: time.sleep(10)
