@echo off
rem Fresh clone? Double-click this. It installs what is needed, tests, and builds MeshyAIStudio.exe right here.
rem Everything else lives in the "source" folder; data and browser profiles are kept there too.
setlocal
cd /d "%~dp0"
call source\tools\build_exe.bat
if errorlevel 1 (pause & exit /b 1)
echo.
echo Done. Start MeshyAIStudio.exe. Models are saved to the Export folder next to it.
pause
