# Master classification (reports 12-22 merged, 2026-10-15)

Source of truth for what to build. Derived from the "Proposed classification" sections of reports 12-22 (reports 01-11 are already merged in `docs/pipeline-catalog.md`). Nothing here was re-scanned from the projects; no Unity Editor verification exists for any row.

**Confidence labels** (per row, taken from the source report's own VERIFIED/INFERRED tags, not re-checked):
- **H** = mostly VERIFIED from file/doc evidence, ideally 2+ projects or official docs.
- **M** = verified in one project, or verified facts with an INFERRED design on top.
- **L** = designed new / INFERRED / unmeasured on device. Needs a pilot before trust.

**Waves** follow the plan (`docs/superpowers/plans/2026-10-15-ai-game-pipeline.md`): W0 conventions + tooling, W1 foundations (rules, framework, UI, art), W2 gameplay/meta systems, W3 orchestration + QA + local batch runner, W4 packaging + pilot.

## 1. Merged rows

Duplicates already merged are noted in the "Merged from" column. Report numbers are in brackets.

### RULE

| Name | Conf | Wave | Depends on | Merged from / note |
|---|---|---|---|---|
| `house-style-core` (short always-loaded CLAUDE.md) | H | W0 | none | [12]; < 200 lines, rest via `.claude/rules/` with `paths:` |
| `workflow-never-overwrite-newer-work` | H | W0 | none | [12] + AGENTS.md parallel-agents section; same as `editor-lane-single-writer` [21] |
| `safety-no-handwritten-unity-yaml` | H | W0 | hook H3 | [12]; enforced by hook, not prose |
| `safety-protected-paths` | M | W0 | hooks | [12]; list is INFERRED, owner confirms |
| `secrets-per-app` | M | W3 | none | [22]; process only (placeholders, local untracked); no secrets-hygiene skill beyond it per user decision |
| `mobile-low-end-defaults` | H | W1 | `device-tier-policy` | [12] + earlier [02] |
| `rule-qa-verdicts-and-validity` | H | W3 | none | [17] |
| `rule-economy-single-source` | M | W2 | none | [16] |
| `rule-bignumber-safety` | M | W2 | none | [16] |
| `ads-layer-contract` | H | W2 | none | [20]; highest revenue risk |
| `analytics-events-taxonomy` (RULE+DATA) | M | W2 | none | [20] |
| `save-and-crash-safety` | M | W2 | data framework | [20] |
| `rule-roblox-single-material` | M | W1 | `roblox-world-shader` | [18]: 1 opaque + 1 alpha material; exceptions for skins/outline/FX/sky |
| `rule-vertex-color-linear` | H | W1 | none | [18] + earlier [11] |
| `rule-roblox-units` | L | W1 | verification backlog in [13] | [13]+[18]; STUD_M = 0.28 is UNVERIFIED |
| `rule-local-substitutes` | M | W2 | none | [13] |
| `combat-hit-detection-rule` | M | W2 | collision registry | [15] |
| `item-data-driven-behavior` | M | W2 | none | [15] (fold into `config-driven-feature`) |
| `character-rig-and-animation-contract` | M | W2 | none | [19] |
| `character-perf-budgets` | L | W2 | device test | [19]; all numbers INFERRED |
| `no-ecs-by-default` (DOTS policy) | M | W1 | none | [14]; hybrid backend only for >100 chasers, approval needed |
| `project-agents-md-template` | M | W0 | none | [14] (Tiny Relax World AGENTS.md structure) |
| `reference-trust-tiers` | H | W0 | none | [14] extends earlier [10] |

### SKILL

| Name | Conf | Wave | Depends on | Merged from / note |
|---|---|---|---|---|
| `pipeline-router` + `clone-orchestrator` | M | W3 | gdd-schema, task graph | [12] pipeline-router and [21] clone-orchestrator are the same entry hub; keep one |
| `gdd-intake` + `gdd-systems-schema` | M | W3 | gdd schemas | [21] + [13]; one skill, schema files as references |
| `roblox-to-unity-map` | M | W2 | `data/roblox-defaults.yaml` | [13] |
| genre playbooks (obby, tower, simulator, tycoon, pet, steal, escape, racing, parkour, mining...) | M | W2 | systems skills | [13]+[14]; one hub with per-genre references, not 25 listed skills |
| `unity-ui` hubs (existing) + `ui-localization` extend | H | W1 | none | [12][20] |
| `unity-data-factory`, `unity-gameplay`, `unity-economy`, `unity-perf-mobile`, `unity-art-import`, `qa-harness`, `release-checklist` | M | W1-W3 | various | [12] hub design: 20-40 listed hubs, recipes as `references/*.md` |
| `economy-auto-balance` | M | W2 | `balance-sim-harness`, `economy-spec-schema` | [16] |
| `qa-fix-retest-loop` | M | W3 | `rule-qa-verdicts-and-validity` | [17]; iteration cap + same-signature stop |
| `unity-ci-quality-gates` | L | W3 | `unity-batch-build` | [22] |
| extend `mobile-build-release` | M | W3 | none | [22] |
| `roblox-world-shader` | L | W1 | palette, surface registry | [18]; design unproven in Editor/device |
| `pet-system` | M | W2 | economy-reference-numbers | [14] |
| `tool-weapon-pipeline` | M | W2 | combat rules | [15] |
| `character-skin-system`, `shop-skin-preview` | M | W2 | rig contract | [19] |
| `meta-systems-checklist` | M | W2 | none | [20] |
| loot/rarity (`economy-progression-design` ext) and hit feedback (`game-feel-polish` ext) | M | W2 | none | [15] |
| movement-abilities, combat-melee-ranged, dig-mine-grid, vehicle-arcade, tycoon-plot | L | W2 | KCC/actor skills | [13]; some overlap with [15]: merge combat-melee-ranged into the [15] tool/combat skills |

### RECIPE

| Name | Conf | Wave | Depends on | Merged from / note |
|---|---|---|---|---|
| `recipe-ads-fake-provider` | M | W2 | `ads-layer-contract` | [20] |
| `recipe-quests-achievements`, `recipe-spin-wheel`, `recipe-retention-timers`, `recipe-settings-pause-update`, `recipe-fake-leaderboard` | M | W2 | meta data | [20] |
| `economy-daily-reward`, `ui-popup-anatomy`, `gameplay-minigame-scaffold` | H/M | W1-W2 | factory pattern | [12] (examples of the recipe form) |
| `recipe-economy-parity-probe` | M | W3 | sim harness | [16] |
| `ui-build-verify-loop` | M | W1 | `ui-validation-rules` | [17] |
| `qa-batch-and-fallbacks` | L | W3 | batch scripts | [17][22] merged: degradation ladder + local batch runner |
| `new-game-from-template` | L | W3 | `game-template-unity` | [22] |
| `kit-pieces-roblox`, `roblox-look-lighting-urp` | L | W1 | world shader | [18] |
| `pet-follow-equip-evolve` (new design), `egg-hatch-loop`, `steal-and-base`, `ride-or-carry-mount` | M/L | W2 | pet-system | [14]; follow/evolve/craft do not exist in any local project |
| `modular-avatar-parts`, `bots-as-players`, `character-emotes-nametags` | L | W2 | character skills | [19]; nametags/emotes designed new |
| tool/combat recipes: health+status, hotbar+inventory UI, throwables/bombs | M | W2 | tool pipeline | [15] |
| roll-rng, fishing, farm-timer, service-loop (minor genre recipes) | L | W2 | none | [13] |

### TOOL

| Name | Conf | Wave | Depends on | Merged from / note |
|---|---|---|---|---|
| `lint_skills.py` (rules L1-L13) | M | W0 | none | [12] = plan Task 1 |
| hook set H1-H9 + `hooks.json` | M | W3 | lint, qa scripts | [12]; Stop-gate loop field unverified, use counter file |
| `agents/*.md` roster (11) | M | W3 | skills | [12]; plugin agents ignore permissionMode/hooks/mcpServers |
| `tools/qa/gate.py` + `run_pipeline` | L | W3 | batch scripts | [12][22] merged; caps: 4 attempts, USD 40 are placeholders |
| `unity-batch-build` (BuildCli, BuildSettingsApplier) | L | W3 | game template | [22] |
| `gdd_lint.py`, `gen_task_graph.py`, `orchestrator.py` | M | W3 | GDD schema | [21] (+ `gdd-lint` [13] is the same tool) |
| `qa-static-checks`, `qa-editmode-validators`, `qa-playmode-smoke` | M | W3 | none | [17] |
| `ui_contract_to_prefab` / `UiSpecBuilder` | M | W1 | ui tokens | [21] + plan Task 10 |
| `balance-sim-harness` | M | W2 | spec schema | [16] + `balance-sim` [14] merged; Python `py -I` vs C# decision lives in [16] |
| `roblox-part-generator`, `roblox-map-bake`, `roblox-world-validate` | L | W1 | world shader | [18] |
| `character-skin-importer` | L | W2 | rig assets | [19] |
| `rarity-enum-generator`, `fog-layer-culling` | M | W2 | none | [14] |
| `meta-wiring-audit` | M | W2 | meta recipes | [20] |
| `dig-terrain-adapter` | L | W2 | none | [15] |
| `unit-converter`, `fake-leaderboard-gen`, `roblox-wiki-scraper` (read-only, ToS-respecting) | L | W2 | none | [13] |
| `sprite-sheet-importer` (2D clones only) | L | defer | none | [14] |

### DATA

| Name | Conf | Wave | Depends on | Merged from / note |
|---|---|---|---|---|
| `docs/agent-handoff.md`, `docs/pipeline/gdd.yaml`, `balance-targets.json`, `run-state/` | M | W0/W3 | none | [12][21]; `pipeline-state.yaml` in plan Task 20 is the same as run-state |
| `gdd-template/`, `gdd-schemas/*.schema.json` | M | W3 | none | [21] + [13] schema outline merged |
| `data/roblox-defaults.yaml`, `genre-templates/*.yaml`, `rarity-tiers.yaml`, `price-tier-map.yaml`, `fake-names.txt` | M/L | W2 | verification backlog | [13] |
| `ui-validation-rules` + perf budgets by tier (`perf-budgets-by-tier`) | M | W1/W3 | none | [17] |
| `world-budgets-by-tier` | L | W1 | device test | [18]; unmeasured |
| `palette-roblox`, `roblox-surface-registry` | L | W1 | none | [18] |
| `economy-spec-schema`, `economy-loop-reference` | M | W2 | none | [16] |
| `economy-reference-numbers.json`, `pet-archetypes.json` | M | W2 | none | [14] |
| tool tiers and upgrade math | M | W2 | none | [15] |
| `character-catalog.json` + `Character_Rig_Asset` | L | W2 | none | [19] |
| `mobile-budgets.json` (size/startup) | L | W3 | none | [22] |
| `game-template-unity` (repo) | L | W3 | none | [22] |

## 2. Cross-report conflicts and corrections to resolve before writing skills

1. **Pool names:** [12] L12 says `PoolManager`/`LeanPool` are stale (use `PoolPrefabGlobal`/`Pool_Manager`); AGENTS.md house style still names `PoolManager`/LeanPool. Plan Task 2 owns the merge wording.
2. **problox:** earlier catalog said SketchEngine + DOTS. [14] corrects: monorepo, DOTS is only the embedded ProjectDawn Agents Navigation crowd backend, no ECS gameplay. Update `docs/pipeline-catalog.md`.
3. **steal-an-egg Spine:** only one tutorial-hand asset; creatures are 3D with Animator. No Spine pipeline needed for Roblox clones ([14], [19] agree: [19] says modular avatar by bone name).
4. **ride-a-pet:** vanhuy engine, PlayerPrefs-JSON persistence breaks house style; use it for ideas only, not as a persistence model ([14]).
5. **One material:** [18] defines it as 1 opaque + 1 alpha, with exceptions. The user's earlier decision stands (one material goal, per-family fallback); [18] is a refinement, not a conflict.
6. **sync.ps1:** [12] verified only `sync.bat` exists; the user-memory note mentioning `sync.ps1` is stale. Fix the memory note or create the script.
7. **Skill count:** the user wants hundreds to 1000+ skills; [12] verified the listing budget (1% of context) makes 1000 listed skills risky. Reconciled design: 20-40 listed hubs + 1000+ reference files (progressive disclosure), which still honors the user's goal.
8. **Combat overlap:** [13] `combat-melee-ranged` vs [15] `tool-weapon-pipeline`/`combat-*`: build [15]'s set, make [13]'s a genre pointer.
9. **Orchestrator naming:** `pipeline-router` [12] vs `clone-orchestrator` [21] vs `game-orchestrator` (plan Task 20): pick one name when writing; recommended `clone-orchestrator`.

## 3. Unverified facts that gate rows (do before trusting)

- 1 stud = 0.28 m and other Roblox constants ([13] verification backlog).
- All device budgets in [18][19][22] (batches, verts, tri counts, size/startup): none measured on a low-end Android.
- Hook behavior: `--settings` hooks under `--bare`; `if` syntax for `Edit(...)`; Stop-hook loop-guard field; unity-mcp compile tool name ([12] section 9).
- `claude plugin eval` availability (server-side kill switch) ([12]).
- Shop 3D preview stage and import validator: designed new, never run ([19]).
- Nothing in 12-22 was checked in the Unity Editor. `ai-game-developer` MCP was down on 2026-10-15; `unity-mcp` was connecting.
