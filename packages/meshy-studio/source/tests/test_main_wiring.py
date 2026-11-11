import os
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MESHY_AUTOSTART"] = "0"


def test_drop_enqueues_job_and_rejects_bad_file(tmp_path):
    from PySide6.QtWidgets import QApplication
    from app.main import MeshyMainWindow
    app = QApplication.instance() or QApplication([])
    window = MeshyMainWindow(project_root=tmp_path)
    img = tmp_path / "a.png"; img.write_bytes(b"x")
    window._enqueue(str(img))
    assert [j.status for j in window.database.list_jobs()] == ["Pending"]
    assert window.jobs_table.rowCount() == 1
    window._enqueue(str(tmp_path / "x.txt"))
    assert window.status.text().startswith("Rejected")
    assert len(window.database.list_jobs()) == 1


def test_windows_explorer_url_drop_queues_all_valid_images(tmp_path):
    from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
    from PySide6.QtGui import QDropEvent
    window = make_window(tmp_path)
    first = tmp_path / "one.png"; first.write_bytes(b"x")
    second = tmp_path / "two.webp"; second.write_bytes(b"x")
    invalid = tmp_path / "notes.txt"; invalid.write_text("x")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in (first, second, invalid)])
    event = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    window.dropEvent(event)
    assert event.isAccepted()
    assert window.database.list_jobs() == []  # dropping only stages: nothing runs before Generate
    assert window.generate_button.isEnabled() and "2 image" in window.generate_button.text()
    assert "notes.txt" in window.reject_label.text()
    window._generate_staged()
    assert {Path(job.image_path).name for job in window.database.list_jobs()} == {"one.png", "two.webp"}
    window._generate_staged()  # nothing staged: still clickable and it says why
    assert "Add images first" in window.status.text()


def test_queue_shows_previews_and_cancels_selected_jobs(tmp_path):
    from PySide6.QtCore import QItemSelectionModel
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication
    from app.main import MeshyMainWindow
    app = QApplication.instance() or QApplication([])
    window = MeshyMainWindow(project_root=tmp_path)
    ids = []
    for index in range(4):
        image = QImage(80, 40, QImage.Format.Format_RGB32)
        image.fill(QColor(40 * index, 100, 200))
        path = tmp_path / f"img{index}.png"
        image.save(str(path))
        window._enqueue(str(path))
    ids = [j.id for j in sorted(window.database.list_jobs(), key=lambda j: j.id)]
    table = window.jobs_table
    assert table.columnCount() == 8 and table.rowCount() == 4
    assert all(not table.item(r, 0).icon().isNull() for r in range(4))  # a preview thumbnail on every row
    rows = {int(table.item(r, 1).text()): r for r in range(4)}
    assert [table.item(rows[i], 3).text() for i in ids] == ["Queued #1", "Queued #2", "Queued #3", "Queued #4"]
    for job_id in (ids[0], ids[2]):  # select two specific jobs
        table.selectionModel().select(table.model().index(rows[job_id], 0),
                                      QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    window._cancel_selected()
    statuses = {j.id: j.status for j in window.database.list_jobs()}
    assert statuses[ids[0]] == statuses[ids[2]] == "Canceled" and statuses[ids[1]] == statuses[ids[3]] == "Pending"
    rows = {int(table.item(r, 1).text()): r for r in range(4)}
    assert table.item(rows[ids[1]], 3).text() == "Queued #1" and table.item(rows[ids[3]], 3).text() == "Queued #2"
    table.selectionModel().select(table.model().index(rows[ids[0]], 0),
                                  QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    window._retry_selected()  # the selection survived the refresh, so both canceled jobs go back
    assert [window.database.queue_position(i) for i in ids] == [3, 1, 4, 2]  # at the back, behind the jobs already waiting


def make_window(tmp_path):
    from PySide6.QtWidgets import QApplication
    from app.main import MeshyMainWindow
    QApplication.instance() or QApplication([])
    return MeshyMainWindow(project_root=tmp_path)


def test_emergency_stop_pauses_the_queue_and_resume_restores_it(tmp_path):
    window = make_window(tmp_path)
    window._owns_runner = False
    for index in range(3):
        image = tmp_path / f"i{index}.png"; image.write_bytes(b"x"); window._enqueue(str(image))
    window._emergency_stop()
    assert {j.status for j in window.database.list_jobs()} == {"Paused"}
    assert "EMERGENCY STOP" in window.status.text() and window.pipeline.halted is True
    window._resume_queue()
    assert {j.status for j in window.database.list_jobs()} == {"Pending"}


def test_pin_account_and_credit_column(tmp_path):
    window = make_window(tmp_path)
    for n in (1, 2):
        window.database.add_account(f"a{n}@x.com", None, n, str(tmp_path / f"p{n}"))
    window.database.set_credit(1, 15)
    window.database.set_credit(2, 115)
    window._refresh_accounts()
    credits = {window.accounts_table.item(r, 0).text(): window.accounts_table.item(r, 2).text() for r in range(2)}
    assert credits == {"a1@x.com": "15 (low)", "a2@x.com": "115"}
    assert "1 account(s) low" in window.alert.text()
    row = next(r for r in range(2) if window.accounts_table.item(r, 0).text() == "a2@x.com")  # the table may be sorted
    window.accounts_table.selectRow(row)
    window._pin_selected_account()
    assert window.pipeline.manual_account_id == window.database.account_by_email("a2@x.com").id
    window._auto_rotation()
    assert window.pipeline.manual_account_id is None


def test_mail_page_lists_added_mailboxes_and_logs_page_reads_the_log(tmp_path):
    import logging
    window = make_window(tmp_path)
    window.mail.add_mailbox("box@purelymail.com", "pw", expires_in_days=2)
    window._refresh_mailboxes()
    assert window.mail_table.item(0, 0).text() == "box@purelymail.com" and "expiring" in window.mail_table.item(0, 2).text()
    logging.getLogger("meshy.test").info("hello password=SECRET123 done")
    for handler in logging.getLogger("meshy").handlers:
        handler.flush()
    window.navigation.setCurrentRow(window.page_names.index("Logs"))
    window._refresh_logs()
    text = window.log_view.toPlainText()
    assert "hello" in text and "SECRET123" not in text  # secrets are redacted in the log file


def test_generate_page_queues_many_files_and_lists_rejections(tmp_path):
    window = make_window(tmp_path)
    good = []
    for n in range(3):
        image = tmp_path / f"ok{n}.png"; image.write_bytes(b"x"); good.append(str(image))
    (tmp_path / "doc.txt").write_text("x")
    queued, rejected = window.enqueue_many(good + [str(tmp_path / "doc.txt"), str(tmp_path / "missing.png")])
    assert queued == 3 and len(rejected) == 2
    assert "doc.txt" in window.reject_label.text() and "missing.png" in window.reject_label.text()
    assert window.recent.count() == 3  # a thumbnail entry per queued image
    assert len(window.database.list_jobs()) == 3


def test_export_folder_and_settings_survive_a_restart(tmp_path):
    window = make_window(tmp_path)
    window.settings.export_dir = tmp_path / "elsewhere"
    page = window.settings_page
    page.concurrency.setValue(1); page.timeout.setValue(45); page.retries.setValue(3)
    page.apply()
    again = make_window(tmp_path)
    assert again.settings.export_dir == tmp_path / "elsewhere" and again.export_label.text() == str(tmp_path / "elsewhere")
    assert (again.settings.job_timeout_minutes, again.settings.max_retries) == (45, 3)
    assert again.pipeline.job_timeout_seconds == 45 * 60 and again.pipeline.max_retries == 3


def test_queue_pause_resume_and_retry_confirmation(tmp_path):
    from PySide6.QtCore import QItemSelectionModel
    window = make_window(tmp_path)
    window._owns_runner = False
    image = tmp_path / "i.png"; image.write_bytes(b"x")
    window._enqueue(str(image)); window._refresh_jobs()
    def select(job_id):
        table = window.jobs_table
        row = next(r for r in range(table.rowCount()) if int(table.item(r, 1).text()) == job_id)
        table.clearSelection()
        table.selectionModel().select(table.model().index(row, 0), QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    job = window.database.list_jobs()[0].id
    select(job); window._pause_selected()
    assert window.database.get_job(job).status == "Paused"
    select(job); window._resume_selected()
    assert window.database.get_job(job).status == "Pending"
    window.database.update_job(job, status="Failed", submitted=1)
    asked = []
    window._confirm = lambda text: asked.append(text) or False
    window._refresh_jobs(); select(job); window._retry_selected()
    assert asked == []  # this is not a confirmation bypass: retry is blocked until server reconciliation exists
    assert "reconcile" in window.status.text().lower()
    assert window.database.get_job(job).status == "Failed" and window.database.get_job(job).submitted == 1


def test_library_lists_filters_and_removes_only_the_record(tmp_path):
    from PySide6.QtCore import QItemSelectionModel
    window = make_window(tmp_path)
    folder = tmp_path / "Export" / "gate_1"
    folder.mkdir(parents=True)
    glb = folder / "gate.glb"; glb.write_bytes(b"glb")
    (folder / "gate.fbx").write_bytes(b"fbx")
    window.database.create_job("a.png")
    window.database.add_model(1, "gate", "a.png", None, str(glb), str(folder), "FBX,GLB", 9449, 1_600_000, None)
    window.database.add_model(2 if window.database.create_job("b.png") else 2, "vase", "b.png", None, str(tmp_path / "gone.glb"), str(tmp_path / "Export" / "vase_1"), "GLB", 100, 10, None)
    library = window.library_page
    library.refresh()
    assert library.table.rowCount() == 1  # the vase record was dropped: its files are not on disk
    assert len(window.database.list_models()) == 1
    window.database.add_model(2, "vase", "b.png", None, str(tmp_path / "gone.glb"), str(tmp_path / "Export" / "vase_1"), "GLB", 100, 10, None)
    library.search.setText("gat")
    assert library.table.rowCount() == 1 and "gate" in library.table.item(0, 1).text()
    library.search.setText(""); library.format_filter.setCurrentText("FBX"); assert library.table.rowCount() == 1
    library.format_filter.setCurrentIndex(0)
    opened = []
    library._opener = opened.append
    library.refresh()
    row = next(r for r in range(library.table.rowCount()) if "gate" in library.table.item(r, 1).text())
    library.table.selectionModel().select(library.table.model().index(row, 0), QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    assert library.open_model() and opened == [str(glb)] and library.open_folder() and opened[-1] == str(folder)
    library._confirm = lambda text: False
    assert library.remove_record() is False and len(window.database.list_models()) == 1
    library._confirm = lambda text: "NOT deleted" in text
    assert library.remove_record() is True
    assert len(window.database.list_models()) == 0 and glb.exists()  # the record went, the file stayed


def test_library_follows_files_deleted_in_explorer(tmp_path):
    window = make_window(tmp_path)
    folder = tmp_path / "Export" / "m_1"; folder.mkdir(parents=True)
    glb, fbx = folder / "m.glb", folder / "m.fbx"
    glb.write_bytes(b"g"); fbx.write_bytes(b"f")
    window.database.create_job("a.png")
    window.database.add_model(1, "m", "a.png", None, str(glb), str(folder), "FBX,GLB", 10, 5, None)
    library = window.library_page
    library.refresh()
    assert library.table.rowCount() == 1 and library.selected_id() is not None  # a row is selected at once
    glb.unlink()  # deleted in Explorer: only the FBX remains
    library.refresh()
    model = window.database.list_models()[0]
    assert model["formats"] == "FBX" and model["file_path"] == str(fbx)
    fbx.unlink()
    library.refresh()  # nothing left: the record is removed
    assert window.database.list_models() == [] and library.table.rowCount() == 0
    seen = []
    library.message.connect(seen.append)
    assert library.open_model() is False and library.open_folder() is False and library.remove_record() is False
    assert seen and all(text for text in seen)  # every button answers, never silently does nothing


def test_logs_filter_and_export_hide_secrets(tmp_path):
    import logging
    window = make_window(tmp_path)
    log = logging.getLogger("meshy.pipeline")
    log.info("job 5 started on account #2")
    log.warning("job 6 failed: token=ABC123 cookie: sessionid=xyz otp 481675")
    log.error("job 7 crashed")
    for handler in logging.getLogger("meshy").handlers:
        handler.flush()
    page = window.logs_page
    page.refresh()
    assert "job 5" in page.view.toPlainText()
    page.level.setCurrentText("ERROR only")
    assert "job 7" in page.view.toPlainText() and "job 5" not in page.view.toPlainText()
    page.level.setCurrentIndex(0); page.needle.setText("job 6")
    target = tmp_path / "exported.txt"
    assert page.export(str(target)) == str(target)
    text = target.read_text(encoding="utf-8")
    assert "job 6" in text and "ABC123" not in text and "sessionid=xyz" not in text and "481675" not in text


def test_selecting_a_nav_item_without_changing_current_row_still_switches_the_page(tmp_path):
    """UI Automation / screen readers 'select' an item; that must open the page just like a mouse click does."""
    window = make_window(tmp_path)
    window.navigation.blockSignals(True)
    window.navigation.item(1).setSelected(True)  # selection only, no currentRowChanged
    window.navigation.blockSignals(False)
    window._on_nav_selected()
    assert window.pages.currentIndex() == 1 and window.page_title.text() == "Queue"
