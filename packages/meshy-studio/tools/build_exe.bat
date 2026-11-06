@echo off
rem Test, build the one-file exe and copy it to the project root (next to data\, profiles\, Export\).
setlocal
cd /d "%~dp0.."
python -m pytest -q || (echo TESTS FAILED - exe not built & exit /b 1)
python -m PyInstaller --noconfirm --distpath dist --workpath build MeshyAIStudio.spec || exit /b 1
copy /Y "dist\MeshyAIStudio.exe" "MeshyAIStudio.exe" || (echo Close the running MeshyAIStudio.exe and run again & exit /b 1)
echo Built: %CD%\MeshyAIStudio.exe
