@echo off
rem Build a small folder for teammates: exe + accounts.txt + readme (~90 MB). The decoder and a browser
rem (if Chrome is missing) are downloaded by the app on first start. No sessions, exports or database.
setlocal
cd /d "%~dp0.."
call tools\build_exe.bat || exit /b 1
set OUT=dist\team\MeshyAIStudio
if exist dist\team rmdir /s /q dist\team
mkdir "%OUT%"
copy /Y MeshyAIStudio.exe "%OUT%\" >nul
copy /Y tools\team_readme.txt "%OUT%\README.txt" >nul
python tools\export_accounts.py "%OUT%\accounts.txt" || exit /b 1
echo Team folder ready: %CD%\%OUT%  (zip/rar this folder; it contains account passwords)
