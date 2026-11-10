# -*- mode: python ; coding: utf-8 -*-
# One-file exe: a single MeshyAIStudio.exe that can be copied next to data/, profiles/, Export/, docs/vendor.

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['keyring.backends.Windows', 'keyring.backends.fail'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['tools/pyinstaller_qt_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Qt 6.12 uses Windows' system ICU. Build environments may have an unrelated ICU on PATH (for example Poppler's ICU 78);
# PyInstaller would collect it as icuuc.dll and QtCore then fails at startup with "specified procedure could not be found".
a.binaries = [entry for entry in a.binaries if not entry[0].lower().startswith("icu")]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MeshyAIStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
