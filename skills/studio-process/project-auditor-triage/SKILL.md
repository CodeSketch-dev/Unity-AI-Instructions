---
name: project-auditor-triage
description: "Run Unity Project Auditor and fix its findings in reviewable batches with a smoke test and step-by-step commits. Use when asked for a project audit, static analysis cleanup, settings diagnostics or a pre-release health pass."
triggers: project auditor, audit project, static analysis, diagnostics, project settings audit, health check, pre release audit, kiem toan du an, quet loi project, don dep canh bao
---

# Project Auditor triage

Source: official (Unity-Technologies/skills/project-auditor-fixes), re-written; [ours] marks additions.

## Prerequisites
Project Auditor package plus its rules package must be installed (without rules a scan is empty or unavailable, never assume "clean"). Run it from the Editor menu (Window > Analysis > Project Auditor) or through MCP/CLI if your setup exposes it; scans are async: trigger, poll status until completed/failed/interrupted (a domain reload interrupts: re-run), one scan at a time.

## Recipe
1. Project opens cleanly; know the baseline Console state. Pick a smoke test (open scene, enter Play, or build) and run it BEFORE any fix.
2. Clean version control state (commit or stash is the owner's call; never discard their changes).
3. Run the audit; export CSV (Category, Severity, Areas, Description, Path, Line, Descriptor, Recommendation).
4. Group by type then by file/subfolder. Work one group at a time.
   - Settings/asset issues (texture import flags, compression, read/write): fix by type, one commit per type or subfolder.
   - Code issues: fix by file; code must compile between commits.
5. Follow the Recommendation column; do not batch unrelated fixes; if a fix fails, revert it before trying another.
6. After each batch: compile, Console clean, smoke test, commit with a clear message (only when commits are permitted for the project).
7. Re-run the audit and report counts before/after per category.

## Rules [ours]
- Triage by impact for mobile: GC allocations in hot paths, texture settings and read/write, shader variants, then style.
- Some findings are false positives for our framework; record them in a short ignore list instead of "fixing".
- Never delete assets just because they are flagged unused: prove it with the project's reference scan first.

## Editor-control gotchas (when driving a CLI/package)
Turn on editor auto-tick before recompiling or running tests unfocused; async commands need polling; method reload needs Play Mode; target one Editor instance explicitly when several are open. Also see `unity-mcp-workflow`.
