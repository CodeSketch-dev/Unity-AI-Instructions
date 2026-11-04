---
name: studio-loop-runbook
description: "Run an autonomous multi-hour studio session: cron wake every minute, backlog file as the single source of truth, code-only subagents + main agent owns the Editor, compile/test/commit gates, no-op while agents run. Use when the owner is away and work must continue until a backlog is done."
triggers: loop, cron, autonomous, backlog, studio, owner asleep, subagent, parallel agents, chay tu dong, ngu
---

# Studio loop runbook

- ONE backlog file (docs/factory/STUDIO-LOOP-<date>.md): ordered checkboxes + append-only LOG + standing practices + links to specs/rules. Every wake: read it, take the first unchecked task. Rules the owner states mid-session go into a docs/ rules file immediately, so another agent or a later session can continue without chat history.
- Cron wake (every minute): if ListAgents shows a running subagent, or the Editor is compiling/playing for someone else, do NOTHING and say so in one line. Otherwise do the next task. CronDelete only when every box is ticked.
- **Progress, not status** (lesson: a wake loop replied "agent still running" for an hour while the agent produced nothing): every wake, read ARTIFACT mtimes (agent notes file, changed prefabs/scripts, report dir; check the PROJECT folder and the repo root, agents sometimes write to the wrong root) and compare with the previous wake. Status `running` is not progress. No artifact change for 10 min = stalled: stop it (TaskStop), then re-scope and re-dispatch smaller. Reply one line only when something changed or a decision is needed; never repeat the same line.
- **Brief sizing**: a subagent has a hard turn budget (about 60 tool calls). One agent = one narrow slice (a group of 2-3 popups or one system), never "everything in the screen plus the checker plus the builders plus a full gate". The brief orders: write the notes file in the first 5 turns and update it after every stage, so hitting the limit never loses the report; then fix in one batch, verify in one pass. An agent that ends at the limit without a report is re-dispatched with a smaller slice, not resumed with the same one.
- **Editor state**: after a subagent ends or is killed, read the Editor state (Play left on? dirty scene?) and fix it. `editor-application-set-state` replies with the OLD state: re-read the state before concluding Play did not stop.
- Roles: subagents are CODE-ONLY (no Editor/MCP/Play/git), each owns an explicit file list; the main agent owns the Editor: refresh, read the Console, run the Editor builders/menus the agents wrote, EditMode, Play screenshots, commit + push. Run independent tasks as parallel agents on disjoint files.
- Gates before ticking: compile clean + Console empty, FULL EditMode green (stale numeric tests after a rebalance are expected: update them and say why), Play screenshot WITH post-processing for anything visual, commit + push. Never repeat an agent claim as verified: agents cannot compile; it is "unverified" until the main agent ran it.
- Agent briefs: files owned, files forbidden, spec/rules docs to read first, exact deliverables, "you cannot compile, do not claim verification". Ask for: files, API signatures, assumptions, what to run.
- After each batch: append LOG, tick boxes, commit docs together with code, publish any new reusable skill (publish.bat) and tell the owner in one line.
- Shell pitfall: file content that itself contains a heredoc terminator or nested quotes breaks `cat <<EOF` blocks. Write such files with the Write tool and edit with Edit; do not nest triple-quoted Python inside a heredoc.
