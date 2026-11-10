---
name: owner-request-ledger
description: Use when the owner sends ANY request, complaint, preference or new task (even mid-task, even a one-liner or screenshot). Log it to docs/owner-requests.md BEFORE acting, never drop it, close only with evidence. Prevents swallowed tasks.
triggers: yeu cau, task, feedback, nuot mat, quen, ghi lai, backlog, cua toi, owner request, ledger, sau nay, lam sau, queue
---

# Owner request ledger (mandatory, every agent, every project)

The owner must never see a request vanish. One append-only file per project: `docs/owner-requests.md`.

## Rules
1. **Log first.** The moment a message contains a request, complaint, preference or idea, add a row BEFORE doing anything else (before tools, before replying): `| OR-### | YYYY-MM-DD | owner words (short, own language) | area | status | evidence/commit | notes |`. One message may create several rows. Screenshot-only messages get a row describing what the owner pointed at.
2. **IDs never change, rows are never deleted or reworded away.** Status only moves: OPEN -> IN PROGRESS (agent/branch) -> DONE (evidence) or BLOCKED (reason) or DROPPED (only if the owner said so; quote them).
3. **DONE needs evidence**: commit hash + the verification that ran (test counts, screenshot path). "Agent said done" is not evidence.
4. **Queue, don't drop.** A new independent request while busy = new row + one-line acknowledgement; finish or hand off current work. Same-objective messages update the existing row.
5. **Every cron / session start / context-compaction recovery**: read the OPEN and IN PROGRESS rows first; take work from them, highest priority first. Final replies list what is still OPEN (count + the top ones).
6. **Subagent briefs** include the OR ids they own and must append status lines for them; the coordinator re-checks the ledger before declaring a lane finished.
7. **Before ending a turn / stopping a cron**: zero OPEN rows, or each remaining row has an explicit reason (BLOCKED / owner-only input). Never stop a loop while rows are OPEN.
8. Concurrent writers: re-read the tail right before appending, add only your own rows, keep line endings.

## Seeding an old project
Mine `docs/feedback-notes.md`, runbooks and the chat transcript once; add rows for every unfinished request; mark verified ones DONE with evidence, unknown ones OPEN.

## Hidden-flag swallow (learned 2026-11)
- Turning a feature off "until reworked" (`const bool X_ENABLED = false`) swallows the owner's task unless the same change adds an OPEN ledger row naming the flag and the rework. Never disable without that row.
- Session-start sweep: grep `= false;` near owner/until/hidden/not finished and match each to an OPEN row; unmatched = swallowed, log it.
- "Code exists" is not "live": verify in Play that the feature actually binds (e.g. `GetComponentInChildren` misses a SIBLING component; search from `transform.root`) before closing a row.
