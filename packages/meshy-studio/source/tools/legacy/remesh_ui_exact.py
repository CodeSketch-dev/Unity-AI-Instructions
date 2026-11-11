from pathlib import Path
import time
from playwright.sync_api import sync_playwright

PROFILE=Path('profiles/account_000001').resolve()
with sync_playwright() as p:
 c=p.chromium.launch_persistent_context(str(PROFILE),channel='chrome',headless=False)
 pg=c.pages[0]; pg.goto('https://www.meshy.ai/vi/workspace',wait_until='domcontentloaded',timeout=60000); pg.wait_for_timeout(3000)
 cards=pg.locator('[data-testid="assets-card"]'); print('CARDS',cards.count(),flush=True)
 card=cards.first; card.click(force=True,timeout=2000); pg.wait_for_timeout(700); card.hover(force=True); card.locator('[data-testid="assets-hover-menu-btn"]').click(force=True,timeout=2000); pg.wait_for_timeout(500)
 edit=pg.get_by_text('Chỉnh sửa mô hình',exact=True); print('EDIT',edit.count(),flush=True); edit.hover(force=True); pg.wait_for_timeout(500)
 menus=pg.locator('[role="menu"]:visible'); print('MENUS',menus.count(),flush=True)
 if menus.count()<2:
  e.hover(force=True); pg.wait_for_timeout(1000); menus=pg.locator('[role="menu"]:visible')
 rem=menus.nth(1).get_by_text('Remesh',exact=True); print('REMESH',rem.count(),flush=True); rem.click(force=True,timeout=2000); pg.wait_for_timeout(700)
 pg.screenshot(path='Export/remesh_menu.png'); print(pg.locator('body').inner_text()[-1200:],flush=True)
 fixed=pg.get_by_text('Cố định',exact=True)
 if fixed.count() and fixed.first.is_visible(): fixed.first.click(force=True,timeout=1000)
 opt=pg.get_by_text('10K',exact=True)
 if not opt.count(): opt=pg.get_by_text('10K',exact=False)
 print('10K',opt.count(),flush=True); opt.first.click(force=True,timeout=2000)
 tri=pg.get_by_text('Triangle',exact=True); tri.click(force=True,timeout=1000)
 ok=pg.get_by_role('button',name='Xác nhận',exact=True); ok.click(force=True,timeout=2000); print('REMESH_10K_STARTED',flush=True)
 for i in range(180):
  pg.wait_for_timeout(5000); body=pg.locator('body').inner_text();
  if i%6==0: print(body[-300:].replace('\n',' | '),flush=True)
  if '10,000' in body or '10K' in body and 'Topology' in body and 'Đang' not in body: pass
 pg.screenshot(path='Export/remesh_ui_final.png');
 while True:time.sleep(10)
