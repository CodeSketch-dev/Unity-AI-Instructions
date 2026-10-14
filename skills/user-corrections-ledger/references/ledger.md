# Corrections ledger (DATA)

Format: `[tag] rule - why - source`. Sources: report 11 notes (N), handoff (H), this repo's feedback notes (F), user decisions 2026-10-15 (D). Dates ISO.

## Art and assets
- [art] Port reference UI/prefab/atlas 100%; generate new art only after proving the reference has none - "close enough" HUD, wrong tiles, improvised icons were rejected - N 2026-10-12
- [art] Never invent a visual a sister project already has (arrow, focus pointer); transfer the closure with an adapter - N
- [art] Procedural art matches the reference silhouette language (voxel, square tips); every tier unique; delete old art - N
- [art] Repeated art = one mesh + vertex colour + shared material, baked in the Editor, authoring kept - N
- [art] Goal: ONE material for the whole world when it renders right; per-family only as fallback - lightest rendering - D
- [art] Do not strip a shader that produced black characters on device; keep OmniShade for skins - N
- [art] Use installed frameworks (Audio, Popup, Taptic); transfer only needed clips; record provenance - N

## Performance
- [perf] No continuous Instantiate/Destroy; pool labels/FX/icons; one manager does label billboard/scale/cull instead of per-object LateUpdate - N standing rule 2026-10-12
- [perf] Do not override scene lighting/ambient at runtime; the scene is the source of truth - agent forced sun 1.5 and the user removed it - N
- [perf] Physics feel: character stays glued to the ground at high speed, no launch, max slope 20 deg - N

## Process
- [process] Wire everything (scene, prefab, SO, refs), run the bake, compile, check Console, Play; build gate before telling the user to build - AGENTS.md, N
- [process] Finish the active task before queued ones; acknowledge and queue new requests - N, promoted into AGENTS.md
- [process] Save the scene after each stage; rebake NavMesh with StartBakingSurfaces then save the scene - persistence failed twice - N
- [process] Back up the dev save before mock purchases and restore after - H
- [process] Skills are developed only in this repo; open Unity projects are reference/test only; ask before writing test artifacts there - F 2026-10-14
- [process] Search the open project (not sibling projects) before generating helpers that may already exist (safe area etc.) - F
- [process] Write files, docs, comments and skills in English, keep skills short and token-lean; chat language stays the user's - F
- [process] Parallel agents: re-read before editing, never overwrite newer work, one writer per scene/prefab - AGENTS.md

## Gameplay and economy
- [econ] Balance is ONE loop (speed, boss, pickaxe, egg HP, pet income, cage, ads, IAP); copy relationships not absolute numbers; fast-forward is QA only; verify from a clean save - N 2026-10-12/13
- [econ] Ads/IAP are optional value, never a paywall; some rewards session-only - N
- [econ] No store-compliance rule for odds; rates are the designer's decision and the agent auto-balances - D 2026-10-15
- [econ] Ads: each app has own SDK keys with one shared mechanism (rewarded, interstitial, banner, app open, native); build a generic ads layer; no secrets-hygiene skill - D
- [game] AI/gameplay reference priority: Steal-an-Egg canon, then knife-tower/monkey-escape, then tune "fun" - N

## UI
- [ui] Fix the text baseline globally in shared setup, not per-label nudges - N
- [ui] UniText vs TMP is an EXPERIMENT (thunder-break-egg tries UniText for performance and easier RTL localization); not a decision, nothing measured, no localization there yet. Do not migrate or claim a winner without a measurement - D 2026-10-15
- [ui] UI must come out beautiful and consistent from the spec alone; mockup/art only supplies style - F 2026-10-14
- [ui] `unity-ui` rules are the standard even when existing prefabs differ; existing prefabs supply parts and styles, not structure - F
- [ui] Layout rules: principles + reason + soft defaults; only user-stated numbers are hard (bottom clearance 200, canvas sort order very high ~30000, joystick touch region 0.35x0.6) - F

## Framework and project
- [framework] SketchEngine = the user's optimized CodeSketch: one framework, versions v1/v2; document the delta - F, D
- [framework] AGENTS.md is the user's experience-based intent; merge wording, do not treat as wrong - D
- [project] knife-tower and monkey-escape hand-coded references; thunder-break-egg vibe-coded but keeps the controlled asset pipeline; climb-tower and bike-obby legacy - F, D
- [project] Local-only games (no server); bots/fake leaderboards substitute for online features - D
- [process] Finish every task item fully (no deferred "not implemented" lists); only Editor-, device- or screenshot-bound verification may remain, stated plainly - D 2026-10-15
- [process] Build the automation (orchestrator, subagents, hooks, gates) rather than formula/calculator content or per-game number tables - D 2026-10-15
