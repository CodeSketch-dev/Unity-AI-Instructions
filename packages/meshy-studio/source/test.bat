@echo off
rem Static check + all automated tests (unit, integration with local fake page / real Blender / real Chrome).
rem GUI test of the built exe (no mouse, no keyboard, no focus):  python tools\gui_exe_test.py
setlocal
cd /d "%~dp0"
python -m pyflakes app tools\meshy_mcp_server.py || exit /b 1
python -m pytest -q %*
