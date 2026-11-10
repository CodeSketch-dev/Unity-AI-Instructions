import os

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
    assert table.columnCount() == 6 and table.rowCount() == 4
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
    assert credits == {"a1@x.com": "15  (low)", "a2@x.com": "115"}
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
    window._refresh_logs()
    text = window.log_view.toPlainText()
    assert "hello" in text and "SECRET123" not in text  # secrets are redacted in the log file
