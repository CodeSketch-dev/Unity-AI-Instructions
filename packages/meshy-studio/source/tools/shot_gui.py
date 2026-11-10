"""Render the main window pages with the real Qt platform (fonts work) into output/shots/."""
import sys, tempfile
sys.path.insert(0, ".")
from pathlib import Path
from PySide6.QtGui import QColor, QImage

import os
os.environ["MESHY_AUTOSTART"] = "0"
from app.main import MeshyMainWindow, create_app

app, w = create_app([])
root = Path(tempfile.mkdtemp())
w.close()
w = MeshyMainWindow(project_root=root)
app.setStyleSheet(app.styleSheet())
for i in range(4):
    img = QImage(120, 90, QImage.Format.Format_RGB32); img.fill(QColor(60 * i, 120, 220)); p = root / f"gate_model_{i}.png"; img.save(str(p)); w._enqueue(str(p))
for n, credit in ((1, 15), (2, 115), (3, 75)):
    w.database.add_account(f"account{n}@example.com", None, n, str(root / f"p{n}")); w.database.set_credit(n, credit)
w.database.mark_account(1, "Quota Limited", cooldown_hours=24)
w.mail.add_mailbox("box@purelymail.com", "pw", expires_in_days=3)
w._refresh_accounts(); w._refresh_mailboxes(); w._refresh_jobs()
w.resize(1180, 760); w.show(); app.processEvents()
out = Path("output/shots"); out.mkdir(parents=True, exist_ok=True)
for i in range(w.navigation.count()):
    pass
for i in range(w.navigation.count()):
    w.navigation.setCurrentRow(i); app.processEvents()
    name = w.navigation.item(i).text().lower().replace(" ", "_").replace("/", "_")
    w.grab().save(str(out / f"{i}_{name}.png"))
print("ok", [w.navigation.item(i).text() for i in range(w.navigation.count())])
