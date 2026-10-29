@echo off
setlocal EnableExtensions
rem ===========================================================================
rem  Sync AGENTS.md + skills to Claude and Codex. Double-click to run.
rem    AGENTS.md  ->  %USERPROFILE%\.claude\CLAUDE.md  va  %USERPROFILE%\.codex\AGENTS.md
rem    skills\*   ->  %USERPROFILE%\.claude\skills\    va  %USERPROFILE%\.codex\skills\
rem    + user settings.json: UI-gate hook enabled, UI skills un-hidden (no name-only)
rem    + every Unity project found next to this repo (and in projects.txt):
rem        CLAUDE.md block, .claude\ai-instructions.md, .claude\skills  (works for cloud sessions too)
rem  Options: /nopause   /nopull (skip git pull)   /nopro (skip per-project step)
rem  Runs git pull --ff-only if the repository is clean; skips pull when there are uncommitted changes.
rem  Differing destination files are overwritten directly; no backup files are created.
rem ===========================================================================
chcp 65001 >nul

set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
rem (REPO must be computed before 'shift', which also shifts %0)
set "NOPAUSE="
set "NOPULL="
set "NOPRO="
:args
if "%~1"=="" goto :args_done
if /i "%~1"=="/nopause" set "NOPAUSE=1"
if /i "%~1"=="/nopull" set "NOPULL=1"
if /i "%~1"=="/nopro" set "NOPRO=1"
shift
goto :args
:args_done

set "SRC=%REPO%\AGENTS.md"
set "CLAUDE_HOME=%USERPROFILE%\.claude"
set "CODEX_HOME=%USERPROFILE%\.codex"
set "RESULT=0"

if not exist "%SRC%" (
    echo ERROR: source file not found %SRC%
    set "RESULT=1"
    goto :finish
)

rem ---- 1. git pull (only when the repository is clean) --------------------------------
if defined NOPULL goto :after_pull
where git >nul 2>&1
if errorlevel 1 (
    echo git not found: skipping pull.
    goto :after_pull
)
set "DIRTY="
for /f "delims=" %%L in ('git -C "%REPO%" status --porcelain 2^>nul') do set "DIRTY=1"
if defined DIRTY (
    echo Repository has uncommitted changes: skipping git pull, syncing from local files.
    goto :after_pull
)
echo Running git pull --ff-only ...
git -C "%REPO%" pull --ff-only
if errorlevel 1 (
    echo ERROR: git pull failed. Fix git first, or rerun with /nopull.
    set "RESULT=1"
    goto :finish
)
:after_pull

rem ---- 2. instructions: AGENTS.md -> Codex + Claude -------------------------------
call :install_file "%CODEX_HOME%\AGENTS.md"
call :install_file "%CLAUDE_HOME%\CLAUDE.md"

rem ---- 3. skills -> Claude + Codex -------------------------------------------
if exist "%REPO%\skills" (
    call :install_skills "%CLAUDE_HOME%\skills"
    call :install_skills "%CODEX_HOME%\skills"
)

rem ---- 4. pipeline agents, commands and hook scripts -> Claude only ------------------------
if exist "%REPO%\agents" call :install_tree "%REPO%\agents" "%CLAUDE_HOME%\agents" "agents"
if exist "%REPO%\commands" call :install_tree "%REPO%\commands" "%CLAUDE_HOME%\commands" "commands"
if exist "%REPO%\hooks" call :install_tree "%REPO%\hooks" "%CLAUDE_HOME%\pipeline-hooks\hooks" "hook scripts"
if exist "%REPO%\ui_gate_reminder.ps1" call :install_tree "%REPO%" "%CLAUDE_HOME%\pipeline-hooks\hooks" "ui gate hook"

rem ---- 5. user settings (hook + skill visibility) and all Unity projects -------------------
set "NOPROFLAG="
if defined NOPRO set "NOPROFLAG=-NoProjects"
if exist "%REPO%\tools\sync_claude_setup.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%\tools\sync_claude_setup.ps1" -Repo "%REPO%" -ClaudeHome "%CLAUDE_HOME%" %NOPROFLAG%
    if errorlevel 1 set "RESULT=1"
)

echo.
if "%RESULT%"=="0" (
    echo Sync complete: instructions + skills + agents/commands + UI-gate hook + Unity projects.
    echo Open a new session to reload.
) else (
    echo Sync finished with ERRORS above; review them.
)

:finish
if not defined NOPAUSE (
    echo.
    pause
)
exit /b %RESULT%

rem ---------------------------------------------------------------------------
:install_file
set "DEST=%~1"
if not exist "%~dp1" mkdir "%~dp1"
if exist "%DEST%" (
    fc /b "%SRC%" "%DEST%" >nul 2>&1
    if not errorlevel 1 (
        echo Already in sync: %DEST%
        exit /b 0
    )
)
copy /y "%SRC%" "%DEST%" >nul
if errorlevel 1 (
    echo ERROR: cannot write %DEST%
    set "RESULT=1"
) else (
    echo Updated: %DEST%
)
exit /b 0

:install_skills
set "SK_DEST=%~1"
if not exist "%SK_DEST%" mkdir "%SK_DEST%"
for /d %%S in ("%REPO%\skills\*") do call :install_one_skill "%%~fS" "%SK_DEST%\%%~nxS" "%%~nxS" "%SK_DEST%"
exit /b 0

:install_tree
robocopy "%~1" "%~2" /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP >nul
set "ROBO=%errorlevel%"
set /a "ROBO_COPIED=ROBO & 1"
if %ROBO% GEQ 8 (
    echo ERROR: cannot copy %~3 to %~2
    set "RESULT=1"
    exit /b 0
)
if %ROBO_COPIED% NEQ 0 echo Updated %~3 -^> %~2
exit /b 0

:install_one_skill
robocopy "%~1" "%~2" /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP >nul
set "ROBO=%errorlevel%"
set /a "ROBO_COPIED=ROBO & 1"
if %ROBO% GEQ 8 (
    echo ERROR: cannot copy skill %~3 sang %~4
    set "RESULT=1"
    exit /b 0
)
if %ROBO_COPIED% NEQ 0 echo Updated skill: %~3 -^> %~4
exit /b 0
