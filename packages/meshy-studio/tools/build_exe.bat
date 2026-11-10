@echo off
rem One command for a fresh clone: find Python 3.11+, install dependencies, test, build the one-file exe and copy it to the
rem project root (next to data\, profiles\, Export\). The exe already contains the default Purelymail key and shared mailbox
rem password (app\mail\default_key.py); nothing has to be typed in afterwards.
setlocal
cd /d "%~dp0.."
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V")
)
if not defined PY (python -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul && set "PY=python")
if not defined PY (echo Python 3.11 or newer is required. Install it from python.org and run again. & exit /b 1)
echo Using: %PY%
%PY% -m pip install -q -r requirements.txt pyinstaller || (echo pip install failed & exit /b 1)
%PY% -m pytest -q || (echo TESTS FAILED - exe not built & exit /b 1)
%PY% -m PyInstaller --noconfirm --distpath dist --workpath build MeshyAIStudio.spec || exit /b 1
copy /Y "dist\MeshyAIStudio.exe" "MeshyAIStudio.exe" || (echo Close the running MeshyAIStudio.exe and run again & exit /b 1)
echo Built: %CD%\MeshyAIStudio.exe
