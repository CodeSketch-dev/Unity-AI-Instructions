@echo off
rem Publish skill/instruction updates (lint, index, router, sync, commit, pull, push). Usage: publish.bat ["commit message"]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\publish.ps1" -Message "%~1"
