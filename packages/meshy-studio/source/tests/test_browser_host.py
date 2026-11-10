import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.browser_host import BrowserHostWidget


def test_browser_host_starts_unhosted_without_launching_browser():
    app = QApplication.instance() or QApplication([])
    host = BrowserHostWidget(object())
    assert host.hosted is False
    assert host.context is None
    host.stop()
    assert host.context is None
    app.quit()

