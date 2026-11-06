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
