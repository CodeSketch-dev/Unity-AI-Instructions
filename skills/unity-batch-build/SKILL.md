---
name: unity-batch-build
description: "Local Unity batch builds and QA gates: BuildCli, pinned Editor, environment signing, size budgets, local runner template and capped claude -p fix loop. Use when building AAB/APK or automating local build checks."
---

# Local Unity batch build and QA gates

This skill automates normal Unity builds on the developer's machine. No remote build service, remote delivery, store upload, tag or push is part of this pipeline. Those outward-facing actions need separate explicit approval.

## Pieces
- `assets/BuildCli.cs.txt` (uncompiled template): `Bootstrap`, `BuildAndroidAab`, `BuildAndroidApk`; reads `-buildVersion -buildNumber -outputDir [-development]`; signing from env vars only, in memory, never logged; exit 0/1; writes `build-report.json` (top assets). Pair with `new-game-bootstrap/assets/BuildSettingsApplier.cs.txt`.
- `scripts/build_cmd.py`: prints or runs the batch command with the Editor pinned in `ProjectVersion.txt`. Blocks when that Editor is missing, an Editor holds the project, or release signing variables are absent (names only are reported).
- `scripts/size_report.py`: artifact size, largest entries, groups, budget and regression gate against `assets/gates.json` and the previous report.
- `assets/local-build.ps1.template`: local PowerShell runner calling preflight, static QA, EditMode, PlayMode smoke, the Unity mobile build and size gate in order. It writes artifacts and logs only under the local project.

## Rules
- Version has one source (`project.config.json`) plus a monotonically increasing build number; do not mix schemes.
- One Unity process per project: build from a separate worktree or close the Editor.
- Do not pass `-quit` with `-runTests`; keep builds synchronous inside one method.
- Symbols zip and mapping files are kept beside the artifact for crash deobfuscation.
- Targets from `assets/gates.json` (size, cold start) are starting budgets. Cold start is measured on a device (`adb shell am start -W`); say so when it was not.
- Verify the current Play requirements (target API, 64-bit, 16 KB alignment of third-party native libraries) at release time instead of trusting memory.

## Headless Claude fix loop (judgement only)
Deterministic local steps (build and test) are scripts. A `claude -p` step may fix compile or test failures caused by files changed in the branch: allow-list tools (Read, Edit, Grep, Glob, read-only git), 8 to 15 turns per call, at most 3 compile-fix and 2 test-fix iterations, never touch ProjectSettings, scenes, prefabs or keystores, never commit, never skip permissions. After the cap, stop and keep the logs locally for review. Details: `references/headless-fix-loop.md`.

Release checklist and store forms: `mobile-build-release`.
