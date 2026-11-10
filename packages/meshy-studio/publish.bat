@echo off
rem Run the tests, build the Windows x64 one-file exe and copy it next to this file.
setlocal
cd /d "%~dp0"
call tools\build_exe.bat
