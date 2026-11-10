import threading

import pytest

from app.automation.meshy_adapter import MeshyWebAdapter

HTML = """<body><div><span>Smart</span> <span>Topology</span></div>
<div id=m><div class=seg><div data-v=a>Meshy&nbsp;7</div><div data-v=b>Meshy N1</div></div></div>
<div><label>Số lượng đa giác</label><div><input id=slider type=range><input id=poly type=text value="30000"></div></div>
<script>document.querySelectorAll('.seg div').forEach(d=>d.onclick=()=>{window.picked=d.dataset.v});</script></body>"""


def _page():
    sync = pytest.importorskip("playwright.sync_api").sync_playwright().start()
    try:
        browser = sync.chromium.launch(channel="chrome")
    except Exception:
        sync.stop()
        pytest.skip("Chrome not available")
    return sync, browser, browser.new_page()


def _body():
    sync, browser, page = _page()
    try:
        page.set_content(HTML)
        MeshyWebAdapter._pick_model(page, "Meshy 7")
        assert page.evaluate("window.picked") == "a"
        field = MeshyWebAdapter._polygon_field(page)
        field.fill("3000")
        assert page.input_value("#poly") == "3000"
    finally:
        browser.close()
        sync.stop()


def test_model_pick_and_polygon_field_by_dom_text():
    errors = []  # Playwright's sync API refuses to run inside another test's asyncio loop: use a clean thread

    def run():
        try:
            _body()
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=run)
    thread.start()
    thread.join(60)
    if errors and isinstance(errors[0], pytest.skip.Exception):
        pytest.skip(str(errors[0]))
    assert not errors, errors
