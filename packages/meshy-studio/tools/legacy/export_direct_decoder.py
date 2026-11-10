from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading, time, base64
from playwright.sync_api import sync_playwright

ROOT=Path('docs/vendor/meshy-ai-to-stl/chrome-extension').resolve(); PROFILE=Path('profiles/account_000001').resolve(); OUT=Path('Export'); OUT.mkdir(exist_ok=True)
page_html='''<!doctype html><iframe id="f" src="sandbox.html"></iframe><script>const f=document.getElementById("f");window.onmessage=e=>{if(e.data?.type!=="go")return;const id=Date.now();const h=x=>{if(x.data?.id!==id)return;window.removeEventListener("message",h);document.title=x.data.ok?"OK":"ERR:"+x.data.error;if(x.data.ok){const a=document.createElement("a");a.download="model14_10k.glb";a.href=URL.createObjectURL(new Blob([x.data.output],{type:"model/gltf-binary"}));document.body.append(a);a.click();}};window.addEventListener("message",h);f.contentWindow.postMessage({type:"convert",id,format:"glb",buffer:e.data.buffer},"*");};</script>'''
(ROOT/'convert.html').write_text(page_html,encoding='utf-8')
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
server=ThreadingHTTPServer(('127.0.0.1',8765),H); threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 ctx=p.chromium.launch_persistent_context(str(PROFILE),channel='chrome',headless=False,accept_downloads=True,downloads_path=str(OUT))
 pg=ctx.pages[0] if ctx.pages else ctx.new_page(); pg.goto('https://www.meshy.ai/vi/workspace',wait_until='domcontentloaded',timeout=60000); pg.wait_for_timeout(5000)
 # select first generated task card (the model card, not example assets)
 imgs=pg.locator('img[src*="api.meshy.ai/misc/cdn-images"]'); print('TASK_IMAGES',imgs.count(),flush=True)
 if imgs.count(): imgs.first.click(force=True,timeout=3000)
 pg.wait_for_timeout(2000)
 # Meshy generates textures as a separate post-process task.
 texture_action=pg.get_by_role('button',name='Kết cấu',exact=True)
 if texture_action.count() and texture_action.first.is_visible() and texture_action.first.is_enabled():
  texture_action.first.click(force=True,timeout=2000); pg.wait_for_timeout(700)
  two=pg.get_by_text('2K',exact=True)
  if two.count() and two.first.is_visible(): two.first.click(force=True,timeout=1000)
  popup_tex=pg.get_by_text('Độ phân giải texture',exact=False).locator('xpath=..').get_by_role('button',name='Kết cấu',exact=True)
  if popup_tex.count() and popup_tex.first.is_visible(): popup_tex.first.click(force=True,timeout=1500)
  print('TEXTURE_STARTED',flush=True)
  for _ in range(180):
   pg.wait_for_timeout(5000); body=pg.locator('body').inner_text().lower()
   if 'độ phân giải texture' not in body and ('đang tạo' not in body or '100%' in body): break
 urls=pg.evaluate("""() => performance.getEntriesByType('resource').map(x=>x.name).filter(u=>/\\.meshy(?:$|[?&])/i.test(u)||u.includes('misc/cdn-models'))""")
 print('MESHY_URLS',len(urls),flush=True)
 if not urls: raise RuntimeError('No authenticated .meshy resource found')
 # Fetch with the authenticated Playwright request context, then transfer
 # bytes to the local decoder page (avoids cross-origin fetch restrictions).
 response=ctx.request.get(urls[0])
 if not response.ok: raise RuntimeError(f'resource fetch failed: {response.status}')
 raw=list(response.body())
 conv=ctx.new_page(); conv.goto('http://127.0.0.1:8765/convert.html'); conv.wait_for_timeout(1000)
 with conv.expect_download(timeout=120000) as di:
  conv.evaluate("b=>window.postMessage({type:'go',buffer:new Uint8Array(b).buffer},'*')",raw)
 download=di.value; target=OUT/'model14_10k.glb'; download.save_as(str(target)); print('GLB_SAVED',target.resolve(),target.stat().st_size,flush=True)
 while True: time.sleep(10)
