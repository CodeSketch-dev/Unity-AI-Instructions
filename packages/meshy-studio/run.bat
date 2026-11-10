@echo off
rem Start Meshy AI Studio from source (uses the project's Python). Use MeshyAIStudio.exe for the built version.
setlocal
cd /d "%~dp0"
python -m app.main
