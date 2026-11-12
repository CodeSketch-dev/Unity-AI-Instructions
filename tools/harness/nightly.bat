@echo off
rem Studio nightly: mine failures + lint hits, run up to 3 backlog tasks unattended, mine again.
rem Never commits, pushes or publishes. Halt with the file %USERPROFILE%\.claude\harness.STOP
cd /d "%~dp0..\.."
python tools\harness\cli.py mine
python tools\harness\cli.py run --agent claude --model haiku --max-tasks 3
python tools\harness\cli.py status
