# Resume here — Unity Roblox clone pipeline

Read this file first, then `docs/agent-handoff.md`, `docs/feedback-notes.md`, and `docs/superpowers/plans/2026-10-15-ai-game-pipeline.md`.

## Goal

Build a local-only agent/skill/hook suite so a game designer can give Claude or Codex a Roblox-clone GDD and the suite can create a Unity mobile clone in about one day, matching the user's existing Unity project conventions.

## Current verified state

- 158 skills; 15 visible hubs; all other skills are `name-only` through `docs/skill-overrides.snippet.json`.
- The skill listing costs 6,923 / 8,000 characters at a 200K-token context (86%).
- `319` Python tests pass and `py -I tools/skill_lint.py --strict skills` is clean.
- Active terminology is **local Unity batch automation** only: normal local compile/test, APK/AAB/iOS build and size/QA checks. Never call this cloud build, CI/CD, deployment or publishing.
- Active QA entrypoint: `qa-batch-and-fallbacks`; gate file: `qa/gates.json`.

## Do next

The safe read-only calibration is complete. Remaining plan work needs an explicit user decision: paid trigger evals (Task 26), creation of a throwaway Unity pilot project (Task 27), and eventual commit. Task 23 remains intentionally excluded. Until one is authorized, only documentation/read-only audits are in scope.

## Do not do without a new explicit user approval

- Do not run `claude plugin eval` or any paid eval.
- Do not create, write to, or modify a Unity project (including a throwaway pilot).
- Do not run `sync.bat` because it writes into the user's Claude/Codex home folders.
- Do not commit, push, publish, upload or deploy.
- Do not implement Task 23 auto-balance: the user does not want formula-heavy/calculator scope.

## Commands

```powershell
$py = 'C:\Users\PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -I -m unittest discover -s tools/tests -p 'test_*.py'
& $py -I tools/skill_lint.py --strict skills
& $py -I tools/skill_budget.py --context-tokens 200000
```

The full test suite needs execution outside the Codex filesystem sandbox because Windows Temp writes are blocked inside it.
