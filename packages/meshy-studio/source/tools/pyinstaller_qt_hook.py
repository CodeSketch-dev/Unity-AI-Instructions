import os
import sys

root = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
for path in (os.path.join(root, "_internal", "PySide6"), os.path.join(root, "PySide6"), root):
    if os.path.isdir(path):
        try:
            os.add_dll_directory(path)
        except (AttributeError, OSError):
            pass
