---
name: agent-team-protocol
description: "Coordinator rules for running many subagents on one Unity project: model tiering, brief template, FIFO Editor lock with heartbeat, keep-compiling, denial handling, report format. Use when dispatching or acting as a subagent on a shared Editor."
---

# Agent team protocol

Operating manual; see `editor-lane-single-writer` (what is serial) and `multi-agent-coexistence` (file conflicts). Use one lock only: this script or another lock skill, never both.

## Coordinator
- **Tiering**: top model only for balance/architecture review and root-cause hunts; cheaper models for builders, test runners, docs, scans; never to poll or summarize logs.
- **Brief** from `references/brief-template.md`: read-first paths (not pasted text), rules, report path, 10-line answer cap.
- **Lanes**: Editor work is serial via the lock; file-only work (C#, tests, docs) runs in parallel on disjoint files (max 4).
- **Collect** report files, not transcripts. Append to shared docs only (re-read the tail first).
- **Denials**: a classifier-denied call stops the agent; it reports the exact call. Never retry, reroute or launder it; ask the user. Pre-authorise routine Editor calls in settings rules; for refresh, the allowed alternative is running `AssetDatabase.Refresh()` via the script-execute tool.

## Editor lock (Play, compile, scenes, prefabs, assets, screenshots)
- `scripts/editor_lock.sh acquire <agent>` queues FIFO (no ticket = starvation); `touch` every ~2 min; `release` always, also on failure. Set `LOCK`/`Q` env to relocate; default is under `Temp/`.
- No heartbeat for 5 min = stale, next ticket takes over (note it in the report). A waiter silent for 2 min leaves the queue.
- **Stay alive while waiting**: run acquire in the foreground with a timeout under the tool limit and repeat it; never end the turn or background it. If it times out, report "blocked on lock held by X". Stop any background job you started (orphans keep tickets).
- Hold for one batch only (compile + run + screenshots), leave Edit Mode.

## Keep the project compiling
- One whole Write/Edit per file; no half-edited state between calls. Do not edit scripts while Play runs (compile stalls): exit Play, edit, recompile. This includes file-only subagents: never launch a script-editing agent while the Editor is in or entering Play (a recompile during Play hung the Editor for 20+ min; only a force-kill recovers, which may need the owner's approval). Order: stop Play, run the agents, wait for them, refresh/compile, then Play.
- Compile under the lock, read the Console, fix your own errors before release. Others' errors: report, do not fix.
- Patch scripts must be idempotent (check for double-applied blocks). Never save a scene with Play-created objects (`playmode-driver-recipes`).

## Report
`docs/reports/<task>.md`: status (DONE / DONE_WITH_CONCERNS / BLOCKED), files, checks run with numbers, unverified items, what others must reload. Final answer: status + path.
