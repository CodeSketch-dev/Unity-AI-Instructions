# AI Game Production Pipeline - design

Status: approved by the user to build in full ("bat dau full", 2026-10-15). Taste decisions only are reserved for the user.

## Intent and why
The studio clones Roblox games into local single-player Unity mobile games. Today one game takes 3-7 days with many prompts, repeated mistakes (UI off from the reference, unwired features, lost decisions) and high token cost. Target: a human documents the Roblox game as a GDD, drops it into Claude, and one pipeline (skills + rules + hooks + subagents + automation, one installable suite) produces a complete game in about 1 day: character, skins, shop, UI, ads, gameplay, economy, QA. The AI should run it with minimal human input, test itself, fix, and re-test until good.

## Goals
- G1 One-prompt UI that is right the first time (no follow-up size fixes): principles and tokens mined from real prefabs, an idempotent builder, a validator, screenshot QA.
- G2 Complete systems coverage for Roblox-style games (see `docs/pipeline-catalog.md` and reports 01-22).
- G3 Very low token cost: progressive disclosure, a small always-loaded index, detail in references/scripts, cheap hooks.
- G4 No repeated mistakes: every recurring correction becomes a rule with its reason.
- G5 Unattended operation: interactive in Claude Code and headless in local batch runner, with iteration caps and resume state on disk.
- G6 Resumable across accounts/sessions: all state in this folder (`docs/agent-handoff.md` first).
- G7 Auto-balance: agent derives and tunes numbers with a simulate-measure-adjust loop and stops at targets or a cap.

## Non-goals
Server/multiplayer, UGC, store-compliance rules about drop odds (designer decides), publishing builds without the user, committing to git without being asked.

## Constraints
- Chat Vietnamese, all files/skills/comments English; terse.
- Framework: SketchEngine (= CodeSketch v2); skills detect version from `Packages/manifest.json` and never invent API of the other version.
- House style from `AGENTS.md` is the user's intent; mined projects refine wording (merge, do not "correct").
- ONE material for the whole game is the goal; per-family materials only as fallback.
- Rules are principles with reasons and soft numeric defaults; deviation needs a stated reason (not hard-fail), except safety rules (data loss, compile, wiring).
- Skills live only in this repo; open Unity projects are read-only references. Idempotent editor tools only; never `InstantiatePrefab` on nested prefabs (caused a 30 GB hang).
- Parallel agents obey `AGENTS.md` "never overwrite newer work" protocol.
- Python launcher is `py`; Unity MCP bridge is ivanmurzak (`unity-mcp`); `ai-game-developer` MCP failed to connect on 2026-10-15.

## Decided by the user (see `docs/feedback-notes.md`)
1 material goal; AGENTS.md wording merge; no odds-compliance rule; shared generic ads layer (per-app keys); start everything now; agent may self-propose missing domains and run them; hundreds to 1000+ skills acceptable.

## Left to the builder
Skill names/grouping, packaging as a plugin, hook details, tool languages (C# editor tools, Python scripts), wave order, how to split tasks across subagents, lint/trigger-eval tooling.

## Inputs
`docs/pipeline-catalog.md` + `docs/pipeline-catalog/01..22-*.md` (22 mined/designed reports), existing `skills/` (49) and `docs/SKILL-SUITE-PLAN.md`.
