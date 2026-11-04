---
name: studio-org-chart
description: "Studio roles in three tiers (directors, leads, specialists), their domain boundaries, escalation paths and which agent to spawn for which task. Use when dispatching agents, writing briefs, or deciding who reviews a result."
triggers: org chart, roles, director, producer, creative director, technical director, who reviews, escalate, which agent, spawn agent, dispatch, to chuc, vai tro, phan cong, giam doc
---

# Studio org chart

Owner = CEO (sets priorities, taste checkpoints). Everything below is autonomous: decide, record a `Ruling:` line, continue. Stop only for irreversible, destructive or security actions. Agent files live in `agents/`; briefs follow `agent-team-protocol`.

## Tiers and who is who
| Tier | Agent | Owns | Never does |
|---|---|---|---|
| Director | `producer` | backlog, LOG, gates, dispatch, claim re-checks | design taste, architecture verdicts, code |
| Director | `creative-director` | pillars, look, feel, hook, monetization fit | code structure, perf numbers |
| Director | `technical-director` | architecture vs KT rubric, SketchEngine-first, prefab-first, lean/mobile rules | taste, balance |
| Lead | `tech-lead` | framework map, plan order, task split | game code |
| Lead | `reviewer`, `qa-tester` | diff review; tests, Console, screenshots | edit game code |
| Specialist | `gameplay-dev`, `ui-dev`, `art-tech`, `release-engineer` | their code/assets inside claimed files | other agents' files |
| Specialist | `game-designer`, `economy-balancer`, `monetization-designer` | specs; numbers; offers and events | SDK or UI code |
| Specialist | `performance-analyst`, `perf-auditor` | measured numbers; static scan | edit code |
| Specialist | `localization-lead`, `analytics-engineer` | text keys and fonts; event taxonomy | layout, SDK internals |

## Domain boundaries (conflicts go up, not sideways)
- Two specialists disagree: their lead decides; leads disagree: the director of the disputed axis decides (feel/monetization = creative, structure/perf = technical, order/scope = producer). Ruling goes into the LOG.
- A director never edits files outside docs/ reviews; a specialist never edits files outside its claim.
- Only the main agent (producer role) drives the Editor, Play, compile, commit; subagents are file-only unless the brief says otherwise (`editor-lane-single-writer`).

## When to spawn which
| Situation | Spawn |
|---|---|
| New feature or system | `game-designer` spec, `tech-lead` plan, then specialists on disjoint files |
| UI task | `ui-dev` (ui-always set), then `qa-tester` audit |
| Numbers, prices, rewards | `economy-balancer` + `monetization-designer`, `creative-director` check |
| Slow / heat / size | `performance-analyst` measure, `perf-auditor` scan, then fix by the owner of the code |
| New text or language | `localization-lead` |
| Tracking / funnels | `analytics-engineer` |
| Before ticking any non-trivial box | `reviewer`; plus the director whose axis the change touches |
| Phase end / release candidate | all three directors in parallel, then `gate-check` |

## How directors review (short, evidence-first)
Input: diff or report file, acceptance numbers, saved screenshot paths. Output: `Verdict: APPROVE|REWORK`, scored axes or rubric IDs with evidence, at most 5 changes, `Ruling:` lines. Creative scores Look/Feel/Hook/Monetization per `studio-boss-quality-bar`; technical runs the KT conformity rubric checks and low-end mobile rules; producer checks that every claim has evidence and that the report file exists. Missing evidence is REWORK, never a soft pass.

## Right-sizing (token cost)
Per `rigor-switch`: `minimal` = producer plus one specialist and `reviewer`, no directors unless the change touches monetization, save format or architecture; `standard` = add the director of the touched axis; `full` = all directors at gates. Never spawn a role that has nothing to decide. Parallel only on disjoint files.

## Briefs and audit
Every brief ends with `Report file: <path>`; hooks warn when a subagent stops without it and log every agent start/stop to `docs/pipeline/agent-log.jsonl`. Directors read the report file, not the chat summary.
