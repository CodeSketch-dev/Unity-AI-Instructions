---
name: game-orchestrator
description: "Run the GDD-to-Unity-game pipeline end to end: lint the GDD, generate the task graph, dispatch subagents by lane, enforce gates and definition of done, keep resumable state. Use when the user hands over a GDD or says build, continue or resume a game clone."
---

# Game orchestrator

You are the producer. Goal: turn a lint-clean GDD into a complete local Unity mobile game in about one day, mostly unattended, with humans only at taste checkpoints. Everything durable lives in files (state, log, GDD, notes), never only in chat. Design: report 21; tools are in `scripts/`.

## Start or resume (always in this order)
1. Read `docs/agent-handoff.md`, `docs/feedback-notes.md`, then `py -I <skills>/game-orchestrator/scripts/orchestrator.py status --project <root>`. No state yet? Go to "Start".
2. `orchestrator.py resume --project <root> --live <agent names still running>` reconciles reality (dead agents, tasks done without evidence). Then `next`.
3. Check Unity: `unity-mcp-workflow` (project and scene confirmed, Console baseline). No MCP connection = say what cannot be verified; never claim Editor results.

## Start
1. `gdd_lint.py <gdd>`: zero BLOCK or stop and run `gdd-intake` to fix (questions go to the human in batches of 4 with a recommended default). WARNs become recorded assumptions in `decisions.md`.
2. `orchestrator.py init <gdd> --project <root>` generates the graph (`gen_task_graph.py`: tasks, skills, agents, claims, verify, groups, estimates, scope cut P2 then P1 when over the day) and the state. Show the human ONE summary (systems, P0/P1/P2 counts, assumptions, estimated hours): checkpoint H1.
3. Phase order and gates: `references/phases-and-gates.md`.

## Loop
`next` -> dispatch -> collect -> `mark` -> repeat. Before Gate G2, the generated balance plan must pass `auto-balance-game` validation and `auto-balance-loop` simulation; after Unity materialization, the same target is checked again on a fresh-save PlayMode path.
- The actual loop is MCP-driven and session-continuous; follow `references/mcp-session-loop.md`. `scripts/pipeline_loop.py` is only the resumable offline controller for GDD/economy evidence and must never promote Unity-dependent stages to pass.
- At every phase boundary, write a compact active-skill manifest with `scripts/skill_context.py`; carry names and reasons only, never full skill bodies. Replace the manifest rather than accumulating prior-phase skills.
- Dispatch consumers may use `orchestrator.py next --json`; each payload carries `active_skills` and the hard `load-only-these-skills` policy, so subagents cannot inherit unrelated phase context.
- Dispatch by lane (`references/parallelism.md`, rule `editor-lane-single-writer`): at most ONE Editor-lane task (agents B and U, everything that touches scenes, prefabs, assets, settings, Play Mode) and up to FOUR file-lane tasks (code, tests, data, docs) in worktrees; never two tasks with overlapping claims.
- Each subagent gets exactly: task text, files and claims, skills to load, acceptance criteria, how to verify, and must return <= 200 words (`subagent roster`: `agents/` in the plugin).
- `mark <id> in_progress` before dispatch, `mark <id> done --evidence "<console clean 12:04>" --evidence "<play step 6 pass>"` after. No evidence, no done. Evidence = tool results (Console, Editor hierarchy/serialized-reference inspection, test run, screenshot diff, validator output), never a claim.
- After each batch: one compile and a Console read; then the QA gates of the phase (`qa-fix-retest-loop`). A failure goes back as a task with its failure signature; three attempts then `blocked` and take the simplest fallback (lower fidelity or cut P2), logged. A balance or PlayMode mismatch must update the owning config, rerun the cheapest failed check, and rerun the affected PlayMode path before it can be marked done.
- Update `docs/agent-handoff.md` after touching shared areas; append user feedback to `docs/feedback-notes.md` immediately.

## Definition of done
Per task: compiled, Console free of new errors/warnings, data -> config -> factory -> prefab/scene wiring complete, serialized refs non-null, acceptance criteria exercised with evidence, no placeholders (`done-means-wired`). Per feature: green on a fresh save AND after restart. Per game: golden path passes from the real entry flow at `timeScale = 1`, every GDD feature done or explicitly cut, provenance complete, shots match at 3 aspect ratios, build gate passes.

## Human checkpoints (taste only; 5 minutes each, never block unrelated work)
H1 scope summary; H2 after the core loop (play 3 min, say feel ok/faster/floatier); H3 after UI (screenshot pairs); H4 final play; H5 optional device. Everything else is decided by agents and logged (`decisions.md`). This repository never creates, copies, uploads, commits, or pushes example/production Unity projects; only an explicitly selected external Unity target may be inspected or changed.

## Budget and scope
Starting guesses per phase in `references/phases-and-gates.md` (recalibrate after the pilot). Over 30% phase overrun: cut P2 automatically and say so. Prefer cutting scope to cutting verification.

Also see: `gdd-schema`, `gdd-intake`, `auto-balance-game`, `auto-balance-loop`, `clone-pipeline` (phase to skills map), `multi-agent-coexistence`, `token-efficient-workflow`, `mcp-session-loop`.
