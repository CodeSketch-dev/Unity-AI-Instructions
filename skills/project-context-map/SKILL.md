---
name: project-context-map
description: Create/maintain docs/PROJECT-MAP.md with an auto-scan script so agents stop re-exploring the repo. Use at project/session start on an unfamiliar codebase, after refactors, or when onboarding Codex/Claude.
---

# Project context map

A 100-150 line map saves thousands of exploration tokens every session and keeps Claude and Codex consistent. The scan script drafts the facts; you add the knowledge only humans and experience supply.

## Create
1. Draft from the code (read-only; write the output outside the project, then copy the edited map into `docs/`):
   ```
   python -I scripts/unity_project_scan.py scan --root <project> --out-json <tmp>/index.json --out-md <tmp>/map.md [--first-party Assets/_Game]
   ```
   `--first-party` prefixes mark your own code so vendor/sample code is excluded from the draft. A big project scans in about a minute.
2. Start from `assets/PROJECT-MAP.template.md` and fold in the draft's scenes, packages, folders, scripts by folder, editor menu tools, asset classes and singleton/event/state types. Trim aggressively: only what an agent needs to navigate and act.
3. Add what the scan cannot know:
   - **Entry flow** (which scene boots, how data loads, how to reach gameplay in Play Mode).
   - **Systems table**: system -> owner class -> file -> prefab -> config asset -> factory entry -> events.
   - **Editor tools**: menu path, what it generates, whether it is idempotent, how to re-run it (`editor-tool-authoring`).
   - **Test shortcuts**: cheat menu, test scenes, timeScale rules, how to reset the save (`debug-cheats-menu`, `unity-qa-playtest`).
   - **Reference mapping**: feature -> reference project path (from `reference-index`).
   - **Gotchas** learned the hard way (things that waste an hour twice).
   - **Current state**: in-progress task, queue, known open bugs (mirror of the feedback notes, 5-10 lines).
4. Keep a pointer to the index file (`reference-index` explains querying) so agents can look up any class/prefab in one command.

## Maintain
- Update the map in the same change that alters a system, entry point, tool or convention; a stale map is worse than none because agents trust it.
- Refresh the draft after large refactors (`scan` again) and diff against the map to see what moved.
- Verify claims before relying on them: file paths in the map can be checked with `Glob`; if one is gone, fix the map.

## Use
Read the map first in every session (and `docs/feedback-notes.md`). Use `query`/`show` on the index for lookups instead of searching the tree. Link the map from the project's AGENTS.md/CLAUDE.md so it is loaded by default.
