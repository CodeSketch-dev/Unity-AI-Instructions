# Feedback notes

## Skills repo (2026-10-14)
- Skills are written in English, short, token-lean; chat stays Vietnamese. Why: lower token cost.
- Layout rules are qualitative (no invented numbers). Only user-stated numbers are kept (bottom clearance 200, canvas sort order ~30000, joystick touch region 0.35x0.6, max left half).
- `unity-ui` rules are the standard even when existing prefabs differ (e.g. popups without a `Root` child). Existing prefabs are reused for parts/styles, not for structure.
- `break-and-steal-unity` is vibe-coded (not a reference). `knife-tower` is hand-coded (reference for conventions).
- Framework pieces (`UISafeArea`, `PopupManager`, `PopupRootSetter`, `Popup`, `ViewContainer`) come from SketchEngine, installed as a git URL package (`com.sketchengine`, lives in `Library/PackageCache`). Skills must say "search first, create only if missing" so other teams' projects don't break.
- Claude tends to regenerate helpers that already exist (e.g. safe area): always search the open project first, never sibling projects.
- Skills are developed only in this repo (Unity-AI-Instructions). Open Unity projects are reference/test only; do not change them to build skills, and ask before writing test artifacts there.
- Goal: new projects built ~3x faster (3 days -> 1 day) with correct output first try. Be flexible: follow the intent, not exact numbers. Root canvas Sort Order only needs to be "very high" (30000 default; existing 25060 is fine, don't change it). Why: values came from earlier vibe setups.
- Toolbar/hotbar (multi-slot bar, contents per game) defaults to bottom-center, above the 200 bottom clearance, no overlap with joystick/interact group.

## UI generation without mockups (2026-10-14)
- Goal: UI must come out beautiful and consistent from an intrinsic spec alone (no mockup); mockup/art ref only supplies style. Why: vibe-coded projects looked near-identical when rules were strict.
- Button anatomy to codify: icon (Image) + TMP in a HorizontalLayoutGroup with Control Child Width on; TMP auto-size shrinks long text; label centred on the button image, lifted slightly when the sprite has a fake bottom shadow/thickness.
- References for mining: knife-tower, monkey-escape (primary, newer), bike-obby, climb-tower (older, layout reference only).

## Mining scope and framework facts (2026-10-14)
- SketchEngine and CodeSketch are ONE framework: the user optimized CodeSketch and renamed it SketchEngine. Treat as versions (older snapshot vs current), document the delta, do not treat as two frameworks.
- Rules must be principle + reason (soft defaults, deviation needs a stated reason), not hard numbers. Many detailed skills are welcome; more detail = better vibe coding. Goal: AI runs the pipeline end to end.
- The mining must cover everything, not only UI: framework, optimization (OptCollisionRegister and why), singletons, object creation/pooling, canvas structure, gameplay systems, economy, tooling, SDK, art pipeline. Classify each finding as rule / skill / recipe / tool / data.
- thunder-break-egg is vibe-coded but must keep the controlled asset pipeline: generated meshes/FBX, ONE shared material, baked vertex colors, optimized scenes.
- Catalog output: docs/pipeline-catalog/01..11-*.md (written by parallel read-only subagents); consolidate into docs/pipeline-catalog.md for user review before any skill is written.
- 2026-10-14: 11 mining reports done; consolidated in docs/pipeline-catalog.md (contradictions with AGENTS.md, risks, build waves, open decisions). No skill written yet; waiting for user review.

## Decisions on the catalog review (2026-10-15)
- Goal is ONE material for the whole game when it renders correctly (Roblox studs texture look = very light). Per-family materials are only the fallback. Why: lightest possible rendering.
- AGENTS.md is the user's own experience-based intent; mined projects show what they actually do with slightly different wording. Reconcile wording (merge), do not treat AGENTS.md as wrong.
- NO store-compliance rule for gacha/jackpot odds: rates are the designer's decision per game, and the agent auto-calculates balance. Skills must make cloning fast and complete; numbers are tuned automatically.
- Each app has its own ad SDK keys, but the setup is the same: shared ads mechanism (rewarded, interstitial, banner, app open, native). Build a generic ads layer skill; no secrets-hygiene skill needed.
- Start the FULL build now. User wants a senior-level, one-suite pipeline: hundreds to 1000+ skills/rules/hooks/agents acceptable if they maximize speed. Agent should self-propose missing domains and run them.
- Target: one full Roblox-clone game (character, skins, shop, UI, ads, gameplay) in ~1 day instead of 3-7 days; very low token cost; no repeated mistakes; UI exactly right from ONE prompt, no follow-up size fixes. No server/multiplayer (local game only).

## UniText vs TMP (2026-10-15)
- UniText in thunder-break-egg is an experiment, not a switch: the user is testing whether it performs better than TMP and whether its right-to-left support (Arabic) makes localization easier. No localization exists there yet and nothing was measured. Why: avoid skills that declare a winner. How to apply: default to TMP in the primary references, use the project's existing component, measure before claiming (profiling-evidence), keep text behind one factory.

## Completeness (2026-10-15)
- Finish every item of a task fully before moving to the next; do not leave a "not implemented yet" list behind. Why: the goal is the strongest possible clone-agent suite, and deferred lists get lost. How to apply: implement all rules/tools in a task scope (Python-testable parts with tests; Editor-bound parts as full templates), and state only what truly needs a Unity Editor or device (not available without MCP) or real screenshots for threshold calibration.

## Reference data volume (2026-10-15)
- The user does not want raw per-game number tables (e.g. another project's pickaxe/bomb tier lists) stored in skills. Why: game-specific, low reuse, token cost; rules stay principles + reasons + soft defaults. How to apply: keep formulas, calculators and a few anchor values; drop full tables; ask before adding raw data dumps.

## Focus (2026-10-15)
- The user wants the pipeline itself: skills/agents/subagents/hooks that turn a new Roblox GDD into a complete Unity game in about 1 day. Formulas, calculators and per-game number tables are NOT wanted. Why: they do not speed up GDD -> game. How to apply: prioritise orchestrator, GDD intake/schema, task graph, subagent roster, hooks and gates, QA automation, bootstrap/local batch runner; keep only procedural skills (how to build X, what to check) and validators that gate automation; no new calculators or data dumps without asking.

## Proactive scope (2026-10-15)
- The user wants anything missing, unfinished, not optimal or absent for building a Roblox game in Unity to be done proactively, in any order, all of it. Why: the goal is a complete pipeline, not a prioritized subset. How to apply: do not ask which gap first; still ask before cost-bearing, destructive, outward-facing or taste/formula-adjacent steps (eval runs cost money, Task 23 auto-balance touches formulas, Unity project creation, commits).
- The user authorized continuing the pending Claude work and running the 12 `claude plugin eval` trigger cases with the previously proposed total cost cap of USD 5.
- Continue autonomously: identify and implement any missing agent, skill, hook, gate or automation needed for the one-day local Unity Roblox-clone pipeline; record resumable progress in the handoff so another agent can continue. Existing boundaries still apply: ask before cost-bearing work, creating/writing a Unity project, commits, or formula-heavy auto-balance scope.

## Local Unity build automation (2026-10-15)
- “local Unity build automation” means local Unity batch automation only: compile/test, build normal mobile APK/AAB or iOS output, and report size on the developer machine. It does not mean remote build service, remote delivery, artifact publishing or store upload. Why: the requested pipeline builds the game normally with Unity, without cloud delivery infrastructure.

## Pilot authorization (2026-10-15)
- The user authorized proactive completion of the vibe-code clone agent, including the throwaway Unity pilot required by Task 27. Why: the goal is a practical agent that can clone Roblox-style games from a GDD, not a collection of untested skills. Continue building missing skills, templates, agents, hooks and automation; retain the existing boundary for paid evaluations unless their cost is explicitly approved.

## Source-control boundary (2026-10-15)
- Keep Unity pilot projects and all Unity runtime tests local-only: do not commit or push them. The shareable deliverable is the suite itself (agents, skills, hooks, tools, tests and docs), so other machines can pull it and continue development. Why: pilot game state is disposable local validation, while the reusable agent pipeline is the collaboration artifact.

## Pilot completion bar (2026-10-15)
- A Unity project that merely opens or passes scaffolding checks is not a pilot game and must not be presented as one. A clone-pipeline pilot is only meaningful when its core loop is playable: authored scene, player, camera, level interaction, HUD and restart path. Why: the user needs a practical vibe-code clone agent, not empty Unity scaffolding.
- A white primitive-cube greybox is not acceptable as a user-facing vibe-code clone result. The generated vertical slice must establish visual identity from the first playable scene: deliberate palette/material treatment, modular geometry, props, lighting and styled HUD; greybox is internal-only. Why: the quality bar is a convincing Roblox-style game, not technical functionality.
- 2026-10-15 | codex | User correction: generic clone skills must not prescribe per-game balance values such as weapon prices, treadmill multipliers, boosts, damage, cooldowns, income, or tier tables. Skills should describe reusable behavior/data/config/wiring contracts; observed values belong only in the per-game GDD when fidelity requires them, and missing balance is generated and validated by the pipeline. Why: documenting numbers wastes tokens and makes generic skills wrong across Roblox clones.
- 2026-10-15 | codex | User requested a real `/auto-balance-game` command with unlimited repeatable parameters. Required inputs include full-game days, daily play hours, per-biome target durations, and extra constraints/overrides; output must cover every stat that affects completion time across money/currencies, progression, combat, content, rewards, retention and rebirth.
- 2026-10-15 | codex | User correction: biome/zone must not be a required model. Auto-balance must support open worlds and arbitrary topology through optional milestone paths, while discovering additional time-sensitive stats from the GDD instead of limiting output to a fixed stat list.
- 2026-10-15 | codex | Token optimization: reduced visible hubs from 16 to 12, regenerated skill overrides/index, and reduced the 200K-context listing from 7,064 to 6,266 chars (88% to 78%).
- 2026-10-15 | codex | User requires every MCP asset refresh/import to stop Unity Play Mode first, wait for an idle Editor, then refresh. This prevents manual stopping and lost/stale Play Mode changes.
- 2026-10-15 | codex | Continued pipeline hardening: added balance-plan validator, materialization contract, routing rule that GDD evidence is required before loading a feature skill, and wired auto-balance into the core-loop gate. Fixed milestone order preservation. Full local test suite: 325 passed; Unity Editor not run.
- 2026-10-15 | codex | User clarified that reference-project-only domains must not become default clone skills. Removed `dig-terrain-adapter`, `treadmill-speed-training`, and `tool-weapon-pipeline`; removed their active routing/index references. Select such mechanics only when evidenced by the current GDD.
