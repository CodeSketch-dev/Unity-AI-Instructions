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

## Lock starvation lesson (do not repeat)
- Launching more than two Editor-bound agents at once starves them: they spend their whole turn budget polling the lock and deliver no result. Cap Editor-bound agents at 2 concurrent; give the rest file-only work (reading code/prefabs, preparing scripts) or start them after the first finish.
- Prefer ONE batch tool that audits/fixes everything in a single Editor call (e.g. an Edit-Mode UI audit of all prefabs writing a report file) over many agents each walking screens by hand; then split the FIX list from the report across at most two agents with short lock holds.
- If the user is playing, the agent must wait or work on files, never stop their Play; the coordinator tells the user once ("stop Play to let the QA run").

## Rubric review: one sub-agent per criterion (idea: FakeMG multi-agent-review)
For a strict review of a diff, plan or test suite: split the rubric into independent criteria and spawn ONE fresh-context sub-agent per criterion, all in parallel, named after the criterion; the coordinator waits idle. Required inputs: rubric, subject, severity scale (Critical / Significant / Minor); missing one = ask before spawning. Each agent reads the whole subject and reports location, problem, impact, fix. Synthesis rules: a section for EVERY criterion (also "zero findings" and "not applicable"), keep every finding ordered by severity, merge two findings only when locations, consequences and fixes are all preserved, run a coverage check (every criterion present) before printing.
