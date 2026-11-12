---
name: agent-hub-codex-workflow
description: "Delegate code work to Codex agents through the owner's agent hub (hubctl.py or ai-agent-hub MCP): brief files, owns paths, non-blocking submit, check progress from disk, never read huge status output. Use when dispatching or reviewing Codex/hub tasks."
triggers: codex, hub, hubctl, ai-agent-hub, sketch-agent-hub, delegate, giao codex, agent codex, submit_task, wait_for_task, owns
---

# Agent hub + Codex workflow
- Claude orchestrates; Codex does file-only code, shader, analysis and doc work. Editor, Play and screenshots stay with Claude (or a Claude subagent).
- Brief = one prompt file in `docs/reports/prompt-<task>.md`: project root, ABSOLUTE paths, owned files (nothing else), goal with evidence, a report path, "no Unity, no git". Mention what was ruled out. Images: Codex must open them by absolute path.
- Dispatch: `python <hub>/hubctl.py run --title T --prompt-file P --cwd ROOT --account N --owns PATH...` in the background (`run_in_background`). It prints the task id and stays alive until done; the launcher finishing is NOT the task finishing.
- Two accounts = two parallel tasks; disjoint `owns` (the hub refuses overlapping running tasks). Never run `codex exec --dangerously-bypass...` yourself; the hub is the sanctioned path.
- Wait by polling the disk, not the hub: loop `for i in $(seq 1 55); do [ -f report ] && break; sleep 10; done` (<10 min per call), then `hubctl.py progress ID` (compact). Old exe builds return 150k-char JSON from get_task_status: avoid.
- After a report: read its conclusion, `assets-refresh`, check Console, verify in Play with screenshots; a Codex "done" is a claim until compiled and seen.
- A stuck "running" row after an MCP/client restart is an orphan (new hub marks it failed); resubmit.
- When the hub misbehaves, fix the hub (owner granted authority) and add a test.

- UI delegation: follow `codex-ui-director-loop` (plan + brief + owned files + capture-based review). Always add "grep usages before removing any symbol".
