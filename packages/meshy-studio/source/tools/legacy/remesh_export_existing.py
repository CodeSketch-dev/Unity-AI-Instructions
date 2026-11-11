from pathlib import Path
import time
from playwright.sync_api import sync_playwright

PROFILE=Path('profiles/account_000001').resolve(); OUT=Path('Export'); OUT.mkdir(exist_ok=True)
EXT=Path('docs/vendor/meshy-ai-to-stl/chrome-extension').resolve()
def vis(l):
    try:return l.count()>0 and l.first.is_visible()
    except:return False
with sync_playwright() as p:
 c=p.chromium.launch_persistent_context(str(PROFILE),channel='chrome',headless=False,args=[f'--disable-extensions-except={EXT}',f'--load-extension={EXT}'])
 pg=c.pages[0]; pg.goto('https://www.meshy.ai/vi/workspace',wait_until='domcontentloaded',timeout=60000); pg.wait_for_timeout(4000)
 for n in ('Đóng','Hiểu rồi','Đã hiểu','Có lẽ sau'):
  l=pg.get_by_text(n,exact=True)
  if vis(l):
   try:l.first.click(force=True,timeout=800)
   except:pass
 imgs=pg.locator('img[src*="api.meshy.ai/misc/cdn-images"]')
 print('TASK_IMAGES',imgs.count(),flush=True)
 if imgs.count():
  imgs.first.click(force=True,timeout=2000); pg.wait_for_timeout(700); imgs.first.hover(force=True)
 edit=pg.get_by_text('Chỉnh sửa mô hình',exact=True)
 if vis(edit): edit.first.hover(force=True,timeout=1000); pg.wait_for_timeout(500)
 rem=pg.get_by_text('Remesh',exact=True); print('REMESH',vis(rem),flush=True)
 if vis(rem): rem.first.click(force=True,timeout=1500)
 fixed=pg.get_by_text('Cố định',exact=True)
 if vis(fixed): fixed.first.click(force=True,timeout=1000)
 opt=pg.get_by_text('10K',exact=True); print('10K',vis(opt),flush=True)
 if vis(opt): opt.first.click(force=True,timeout=1000)
 tri=pg.get_by_text('Triangle',exact=True)
 if vis(tri):
  try:tri.first.click(force=True,timeout=1000)
  except:pass
 ok=pg.get_by_role('button',name='Xác nhận',exact=True)
 if vis(ok): ok.first.click(force=True,timeout=1500); print('REMesh_10K_OK',flush=True)
 pg.wait_for_timeout(3000); pg.screenshot(path=str(OUT/'model14_remesh10k.png'))
 sw=c.service_workers
 if sw:
  ident=sw[0].url.split('/')[2]; ex=c.new_page(); ex.goto(f'chrome-extension://{ident}/automation.html'); ex.wait_for_timeout(15000); print('EXT',ex.title(),flush=True)
 while True:time.sleep(10)
