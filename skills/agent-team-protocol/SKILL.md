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

## Delegation hygiene (learned from stalled UI rounds)
- **Slice by turn budget**: a subagent gets ~60 tool calls. Give one slice (2-3 popups / one system). Never combine fixing content, fixing the checker and porting to builders in one brief.
- **Report paths absolute**: the brief names the full report path inside the PROJECT folder; the agent writes it by turn 5 and updates it after each stage. The coordinator checks both the project folder and the repo root when a report seems missing.
- **Verify progress by files**: judge an agent by artifact mtimes (notes, changed assets), not by its `running` status. 2 min without a change (owner limit; the agent touches its notes file after every stage) = stop and re-scope.
- **Looking is part of done**: for visual work the brief requires saved screenshots that the agent looks at and the coordinator opens too; audit numbers alone never close a visual item (`ui-visual-qa`).
- **Do not repeat measurements**: one audit per case unless a fix happened in between (`qa-fix-retest-loop`).
- After an agent ends or is killed, restore the Editor (exit Play, scene not dirty, save restored) before dispatching the next.

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

## Brief checks (added after an agent skipped its required skills)
- The brief makes the agent's FIRST notes line `Skills read: <names + one fact from each>`; the coordinator rejects a report with `Skills read: none`.
- A "before/after" evidence pair must be two different captures. A copy or a missing "after" capture = the fix is NOT verified, whatever the agent concludes.
- An agent that classifies audit findings as false positives must name the checker rule and show numbers (pair centre vs frame); the checker is then fixed (measure icon+label pairs) instead of ignoring the finding.
