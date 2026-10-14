---
name: feedback-notes-sync
description: Keep docs/feedback-notes.md as durable log and task queue of user corrections and queued requests. Use at session start, on every correction/preference, and when a request arrives mid-task.
---

# Feedback notes and task continuity

Long vibe-coding sessions lose information at context compaction and when another agent takes over. A short file in the repo is the cheapest fix.

## Session start
Read `docs/feedback-notes.md` (create it if missing, with sections: Gameplay/Features, Visuals/UI, Reference projects, Process, Queue). Resume any item marked QUEUED or IN PROGRESS.

## While working
- On each correction, preference, design decision or rejected approach, add or update a concise dated bullet under the right topic: `- YYYY-MM-DD: <rule> (why: <reason the user gave>)`. Update an existing bullet instead of duplicating.
- Write it when it arrives, not at the end.
- Mark status in-line: `(DONE YYYY-MM-DD)`, `(QUEUED after <task>)`, `(BLOCKED: <reason>)`.

## Queue discipline
- Finish the current authorized task, including wiring and verification, before starting a new one.
- A message about the same objective is a correction to the current task; an independent request goes to the queue with a one-line acknowledgement.
- Only reprioritize or drop work when the user explicitly says so.
- Keep outstanding items visible in replies so nothing silently disappears.

## Concurrent writers
Claude and Codex both append here. Re-read the tail right before appending, add or change only your own lines, preserve line endings, never rewrite the whole file. Task handoffs between agents go in `docs/agent-handoff.md` (`multi-agent-coexistence`).

## Style
Facts and rules, not narrative. One or two lines per entry, in the language the team uses. Don't store what is derivable from code or git history.
