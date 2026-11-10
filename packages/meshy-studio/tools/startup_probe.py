"""Measures main-thread stalls after the window is shown (heartbeat every 50 ms)."""
import os, sys, tempfile, time
os.environ["MESHY_AUTOSTART"] = "0"
sys.path.insert(0, ".")
from pathlib import Path
from PySide6.QtCore import QTimer
from app.main import MeshyMainWindow, create_app
t0 = time.time()
app, w = create_app([])
w.close()
w = MeshyMainWindow(project_root=Path(tempfile.mkdtemp()))
print(f"construct {time.time() - t0:.2f}s", flush=True)
w.show()
shown = time.time()
last, worst = [time.time()], [0.0, 0.0]
def beat():
    now = time.time()
    gap = now - last[0]
    if gap > worst[0]:
        worst[0], worst[1] = gap, now - shown
    last[0] = now
timer = QTimer(); timer.timeout.connect(beat); timer.start(50)
QTimer.singleShot(25000, app.quit)
app.exec()
print(f"worst main-thread stall: {worst[0]:.2f}s at +{worst[1]:.1f}s after show", flush=True)
