"""Every button in the app must be clickable and must DO something visible (status text, label, view or data change)."""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MESHY_AUTOSTART"] = "0"

SKIP = {"EMERGENCY STOP"}  # exercised in test_pipeline / GUI test: it halts the whole queue (covered separately below)


DIALOGS = []  # a button that opens a dialog (here cancelled) has responded


def _stub_dialogs(monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    DIALOGS.clear()

    def stub(result):
        return staticmethod(lambda *a, **k: DIALOGS.append(1) or result)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", stub(("", "")))
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", stub(([], "")))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", stub(""))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", stub(("", "")))
    monkeypatch.setattr(QInputDialog, "getText", stub(("", False)))
    monkeypatch.setattr(QInputDialog, "getInt", stub((0, False)))
    monkeypatch.setattr(QMessageBox, "question", stub(QMessageBox.StandardButton.No))


def _snapshot(window):
    from PySide6.QtWidgets import QLabel, QPlainTextEdit
    texts = [label.text() for label in window.findChildren(QLabel)] + [view.toPlainText() for view in window.findChildren(QPlainTextEdit)]
    return window.status.text(), tuple(texts)


def test_every_button_is_enabled_and_responds(tmp_path, monkeypatch, _no_real_launches):
    from PySide6.QtWidgets import QApplication, QPushButton
    from app.main import MeshyMainWindow
    app = QApplication.instance() or QApplication([])
    _stub_dialogs(monkeypatch)
    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda *a: errors.append(a[1]))
    window = MeshyMainWindow(project_root=tmp_path)
    window.show()
    silent, disabled = [], []
    for button in window.findChildren(QPushButton):
        text = button.text().strip().replace("\n", " ")
        if text in SKIP or not button.isVisibleTo(window) and not button.parent():
            continue
        if not button.isEnabled():
            disabled.append(text)
            continue
        window.status.setText("")
        before, dialogs = _snapshot(window), len(DIALOGS)
        button.click()
        app.processEvents()
        if _snapshot(window) == before and len(DIALOGS) == dialogs:
            silent.append(text)
    assert not errors, errors
    assert _no_real_launches, 'Open folder must have been invoked (into the stub, never a real Explorer window)'
    assert not disabled, f"buttons that cannot be clicked: {disabled}"
    assert not silent, f"buttons that did nothing visible: {silent}"


def test_emergency_stop_button_halts_and_resume_restores(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QPushButton
    from app.main import MeshyMainWindow
    app = QApplication.instance() or QApplication([])
    window = MeshyMainWindow(project_root=tmp_path)
    window._owns_runner = True  # as the real app that holds the runner lock
    monkeypatch.setattr(window.pipeline, "start_background", lambda: None)
    buttons = {b.text(): b for b in window.findChildren(QPushButton)}
    buttons["EMERGENCY STOP"].click(); app.processEvents()
    assert window.pipeline.halted
    buttons["Resume queue"].click(); app.processEvents()
    assert not window.pipeline.halted
