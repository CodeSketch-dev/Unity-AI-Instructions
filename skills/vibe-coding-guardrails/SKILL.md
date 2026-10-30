---
name: vibe-coding-guardrails
description: Always-on checklist of basic AI mistakes in Unity vibe coding (guessing, huge greps, Editor timeouts, wrong rename/delete scope, skipped UI skills, unverified claims, token waste) with the habit that prevents each. Use at the start of every task and before reporting done.
---

# Vibe-coding guardrails (read at task start, 1 minute)

Each rule comes from a real mistake. Follow the habit, it is cheaper than the redo.

## Understand before acting
- Ambiguous word (which button, "hidden component", "old store code")? Inspect the real thing first (Play Mode dump, `git grep`, the spec PDF/sheet the user attached) and say your reading in one line. Never delete or refactor on an assumed meaning; a wrong premise cost a full refactor round once.
- The user attached a doc/PDF/screenshot: it is the source of truth. Extract it first (spec-pdf-extract), compare every row against the game, list mismatches. Do not claim "matches the doc" without a table.
- A new request mid-task: finish the current task, queue the new one, acknowledge in one line (AGENTS.md).

## Do not waste tokens or time
- Search narrow: `Grep` with `files_with_matches` + `head_limit`, scoped to `Assets/_Game/Scripts` (or graphify query/path/explain first). Never `grep -r`/`find` over all of `Assets` or `Library` (>120 s timeouts, huge output).
- Do not re-read a file you just edited, do not paste big YAML/logs into context, read ranges (offset/limit). Batch independent tool calls in one message.
- One audit script per screen: a single `script-execute` that opens the tab, counts components, reads texts/colours/interactable and logs once; read the Console once per step, filtered (`Error`, `lastMinutes`).
- Long QA/refactor: give each subagent ONE narrow scope (one minigame, one prefab family) and tell it to deliver its report before its turn limit (about 40 tool turns). Never launch one agent for "everything".
- Do not ask the user what you can read from the repo; ask only for real design forks, with a recommended default.

## Unity / Windows traps
- `assets-refresh` timing out means Unity is still compiling/importing, not failure: poll `editor-application-get-state` until `IsCompiling=false`, then read errors. Never start Play or edit while compiling.
- Before Play/refresh/tests take the Editor lock (`docs/tools/editor_lock.sh acquire <name>`), stop a leftover Play Mode first, release in Edit Mode with scenes not dirty. Do not stay in Play when you finish.
- Renaming assets: `git mv` the file AND its `.meta` (keeps GUID), then update string references (`Resources.Load("...")`, builders, tests, `m_Name` of the prefab root). Grep the old name afterwards and compile.
- Removing a component from a prefab family: check variants/nested instances and every consumer (`GetComponent`, serialized fields) first; use an Editor migrator, never YAML surgery. Back up (`git diff > docs/backup-*.patch` + copy prefabs outside Assets) before bulk changes.
- Python may be missing or user-site only: `python -m pip install --user`, then run without `-I`. Git Bash paths are `/d/...`. `sed -i` on CRLF files is fine but keep line endings; PowerShell 5.1 reads BOM-less files as ANSI, so keep `.ps1` hook scripts ASCII (use `\uXXXX` in regexes).
- Runtime-built UI (shops that clone or rebuild cards at runtime) cannot be judged from the prefab: verify in Play Mode.

## UI work is never "small"
- Any button/label/icon/price/popup/animation change: load `ui-always` FIRST (the router hint says so), build with layout groups, measure dx/dy <= 1 px and textBounds inside rect by script, then look at a screenshot. Icon + price = one centred HorizontalLayoutGroup (`ui-icon-label-layout`). Buttons need press anim + sfx (`ui-button-anatomy`); price buttons follow `price-button-contract`; no `$` on in-game money.
- Changing an animation/scale/colour value still needs the Play check (sample twice) and a screenshot.
- Any screenshot/test/console result that shows a UI defect triggers the matching skill and a fix at once (auto-fix loop in `ui-always`); never wait to be asked.

## Prove it, then say it
- Done = wired + compiled + Console clean + exercised in Play (done-means-wired, verification-before-completion). Say plainly what was NOT verified; never write PASS without evidence; a subagent report is a claim, spot-check one fact yourself.
- Report in the user's language, short: what changed, how verified, what is left. Offer the next step as one question with a recommended default.
