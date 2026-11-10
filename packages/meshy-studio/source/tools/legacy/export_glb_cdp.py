from pathlib import Path
import subprocess, time
from playwright.sync_api import sync_playwright

PROFILE=Path('profiles/account_000001').resolve(); EXT=Path('docs/vendor/meshy-ai-to-stl/chrome-extension').resolve(); OUT=Path('Export'); OUT.mkdir(exist_ok=True)
chrome=Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'); port=9223
subprocess.Popen([str(chrome),f'--remote-debugging-port={port}',f'--user-data-dir={PROFILE}',f'--disable-extensions-except={EXT}',f'--load-extension={EXT}','https://www.meshy.ai/vi/workspace'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
with sync_playwright() as p:
 b=None
 for _ in range(60):
  try:b=p.chromium.connect_over_cdp(f'http://127.0.0.1:{port}');break
  except:time.sleep(.25)
 if b is None: raise RuntimeError('CDP unavailable')
 c=b.contexts[0]; pg=c.pages[0]; pg.wait_for_timeout(5000)
 if not c.service_workers:
  try:c.wait_for_event('serviceworker',timeout=10000)
  except:pass
 print('WORKERS',[w.url for w in c.service_workers],flush=True)
 # Select first generated Meshy task card and close overlays.
 for n in ('Đóng','Hiểu rồi','Đã hiểu','Có lẽ sau'):
  l=pg.get_by_text(n,exact=True)
  try:
   if l.count() and l.first.is_visible():l.first.click(force=True,timeout=700)
  except:pass
 imgs=pg.locator('img[src*="api.meshy.ai/misc/cdn-images"]')
 if imgs.count(): imgs.first.click(force=True,timeout=2000)
 pg.wait_for_timeout(1500)
 if not c.service_workers: raise RuntimeError('extension service worker did not start')
 sw=c.service_workers[0]; ident=sw.url.split('/')[2]
 ex=c.new_page(); ex.goto(f'chrome-extension://{ident}/automation.html'); ex.wait_for_timeout(20000)
 print('EXT_TITLE',ex.title(),flush=True)
 print('EXPORT_DIR',[x.name for x in OUT.glob('*')],flush=True)
 while True:time.sleep(10)
