---
name: parallel-qa-fanout
description: How to QA and fix many screens, modes or minigames with subagents on a single-writer Unity Editor without running out of turns or losing the Editor lock. Use when asked to QA or fix several modes, shops or screens in parallel.
triggers: qa all, test all, fan out agents, subagent qa, qa toan bo, kiem tra tat ca, nhieu agent
---

# Parallel QA fan-out

Lessons: one agent asked to test everything ran out of turns with no report; parallel agents fought for the single Editor and lost their time-boxed locks; several agents edited the same shared files.
1. One agent = one mode/screen family. Brief = a shared rules file + 5 lines of scope. Cap about 40 tool turns and tell the agent to deliver its report by turn ~35 even if incomplete (list UNVERIFIED).
2. The Editor is single-writer. Prepare scripts/checklists/expected values BEFORE acquiring the lock; hold <= 15 min; heartbeat; release in Edit Mode with scenes clean and saves restored. With more than 2 agents needing the Editor, run them in sequence instead of idling on the queue.
3. One dump script per screen: open it, log component counts, texts, colours, interactable, scale (sampled twice) in one call; read the Console once, filtered to Errors.
4. Shared files: fix small, announce in the report, and make the owners of the other screens re-run. The coordinator does ONE compile + Console + test run at the end and spot-checks one claim per report.
5. Compare against the design sheet row by row (mismatch table), never "looks right".
6. QA is not only reporting: when a capture shows misaligned/overlapping/tiny UI, apply the UI skills and fix it in the same pass (`ui-always` auto-fix loop).
7. Report in the user's language: screen x PASS/FAIL/UNVERIFIED, bugs, files changed, what remains.
