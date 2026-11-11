@echo off
rem Register the Meshy MCP server with Claude Code and Codex (user scope). Run once per machine.
rem Needs Python 3.11+ (standard library only for the server) and the claude / codex CLIs on PATH (each is optional).
setlocal
cd /d "%~dp0.."
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (for /f "delims=" %%P in ('py -%%V -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P")
)
if not defined PY (for /f "delims=" %%P in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P")
if not defined PY (echo Python 3.11 or newer is required. & exit /b 1)
set "SERVER=%CD%\tools\meshy_mcp_server.py"
echo Python: %PY%
echo Server: %SERVER%
where claude >nul 2>nul && (claude mcp remove meshy --scope user >nul 2>nul & claude mcp add --scope user meshy -- "%PY%" "%SERVER%" && echo Registered with Claude Code) || echo claude CLI not found: skipped
where codex >nul 2>nul && (codex mcp remove meshy >nul 2>nul & codex mcp add meshy -- "%PY%" "%SERVER%" && echo Registered with Codex) || echo codex CLI not found: skipped
echo Restart Claude Code / Codex sessions to load the tools. Keep MeshyAIStudio.exe running for generation.
