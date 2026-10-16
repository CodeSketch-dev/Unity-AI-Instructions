---
name: agent-team-protocol
description: "Coordinator rules for running many subagents on one Unity project: model tiering, brief template, FIFO Editor lock with heartbeat, keep-compiling, denial handling, report format. Use when dispatching or acting as a subagent on a shared Editor."
---

# Agent team protocol

Complements `editor-lane-single-writer` (what is serial) and `multi-agent-coexistence` (file conflicts). This skill is the operating manual: how to brief, lock, queue and report. If `parallel-subagents-unity-lock` is installed, its lock file may be used instead of the script here; never run both on one project.

## Coordinator
1. **Model tiering**: strongest model only for balance/architecture review and root-cause hunts; cheaper models for builders, test runners, docs, scans. Never use the top tier to poll or to summarize logs.
2. **Brief** every subagent from `references/brief-template.md`: read-first list (paths, not pasted text), rules, process, report path, final-answer length cap (10 lines). Ask for conclusions, not dumps.
3. **Lanes**: Editor-touching tasks are serial through the lock; file-only tasks (C#, tests, docs, Python) run in parallel on disjoint files (max 4).
4. **Collect**: read report files, not transcripts. Append to shared docs only (re-read the tail first).
5. **Denials**: if a permission classifier denies a subagent call, the agent stops and reports the exact call. The coordinator never repeats, reroutes or launders a denied action (no "do it via another tool"); ask the user.

## Editor lock (any agent touching Play, compile, scenes, prefabs, assets, screenshots)
- Use `scripts/editor_lock.sh acquire <agent> <task>`; it takes a ticket, waits FIFO, writes a heartbeat; `release` always, also on failure; `touch` every ~60 s in long sessions.
- A lock whose heartbeat is older than 5 min is stale: the next in queue takes over and notes it in the report.
- **Never end your turn while waiting** for the lock or a background job: poll with short sleeps, or hand back a "blocked on lock held by X" report. No orphan background jobs: stop what you started.
- Hold the lock for one batch only (compile + run + screenshots), then release.

## Keep the project compiling
- Write a whole file once (one Write/Edit), never leave it half-edited between calls. Compile under the lock, read the Console, fix your errors before releasing.
- Patch scripts that mutate files must be idempotent; check for a double run (duplicate blocks) before compiling.
- Never fix compile errors in a file another agent owns: report it.
- Never save a scene while Play-created objects exist (see `playmode-driver-recipes`).

## Report format (file, not chat)
`docs/reports/<task>.md`: Status (DONE / DONE_WITH_CONCERNS / BLOCKED), files changed, checks actually run with numbers, what is unverified, what others must reload/re-read. Final answer: that status plus the path.
