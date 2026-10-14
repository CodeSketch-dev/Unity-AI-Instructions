# 21 - GDD package schema, GDD intake, and the unattended clone orchestrator

Status: design proposal (nothing implemented, nothing run in Unity). Author role: producer + technical designer. Builds on: `clone-pipeline`, `spec-then-plan`, `gameplay-video-analysis`, `game-clone-recon`, `reference-index`, `project-context-map`, `token-efficient-workflow`, `spec-pdf-extract`, `ui-clone`, catalog 06/07/11, `docs/feedback-notes.md`, and the thunder-break-egg spec/plan format ("Decisions taken with the user" table with a Why column, "Reference facts" tables with anchor/pos/size, acceptance checkboxes, plans with Files / Interfaces / Steps / How+Expected, a final integration task, a Review-focus list).

User goal in one line: a human documents a Roblox game 1:1 (numbers may differ slightly), drops the doc in, and a mostly unattended pipeline returns a complete wired Unity clone in about one day.

Design principles (each one answers a recorded failure):
1. The GDD is the only per-game input. Skills stay generic (as `clone-plan.md` already says); the GDD replaces hand-written `clone-plan.md` + `gameplay-analysis.md` and generates them.
2. Every claim carries evidence (capture id + timestamp) or an explicit `source: free`. No evidence, no `exact`.
3. Structured front-matter for machines, prose below for humans. Agents read front-matter only unless a task needs the prose (token cost).
4. The linter is the gate between human work and agent work. Cheap to run, fails loudly, produces a question list instead of guesses.
5. Anything the agent decides alone is written to `decisions.md` with a reason (survives compaction).

---------------------------------------------------------------------------------------------------
## 1. GDD package format

### 1.1 Folder layout (lives in the target Unity repo root, read-only for agents except `gdd/_generated/`)
```text
gdd/
  00-index.md              # manifest: game identity, global tokens, system list, priorities (front-matter is the contract)
  decisions.md             # append-only: human + agent decisions, each with Why (thunder-break-egg style)
  glossary.md              # names as shown in game ("Rebirth", "Gems") -> canonical ids; localization keys source
  systems/                 # one file per system, id S-<nn>-<slug>.md, front-matter per section 1.3
    S-01-character.md  S-02-camera.md  S-03-input.md  S-04-world-zones.md  S-05-checkpoints.md ...
  ui/                      # one file per screen/popup/HUD: UI-<nn>-<slug>.md  (layout contract, section 1.4)
    UI-00-hud.md  UI-10-skin-shop.md  UI-11-settings.md ...
  economy/                 # numbers as tables a script can read
    currencies.md          # front-matter list; prose = sinks/sources
    prices.csv  drops.csv  curves.md  rewards.csv  timers.csv
  assets/
    assets.csv             # id,kind,name,source(own|ref-project|generate|buy),path_or_prompt,used_by,license
    style.md               # palette, shape language, material policy (links to catalog 11 rules)
  captures/                # evidence: CAP-<nnn>.jpg|mp4-frames, plus captures/index.md
    index.md               # id | file | video | mm:ss | what it proves | device/version
  qa/
    golden-path.md         # the 3-minute playthrough as steps (becomes the PlayMode script)
  _generated/              # written by tools only: lint-report.md, gdd.json (merged), task-graph.json, questions.md
```
Human-writable minimum: `00-index.md` + `systems/*.md` + `ui/*.md` + `economy/*.csv` + `captures/`. Everything else may be generated or stubbed by the intake skill.

### 1.2 Conventions shared by every file
- File = YAML front-matter (machine) + optional prose (human notes, `## Notes`, `## Open questions`). Agents never need the prose to execute a task.
- Ids: `S-<nn>-<slug>` system, `F-<nn>.<m>` feature (inside a system), `UI-<nn>`, `E-<name>` table, `A-<nnn>` asset, `CAP-<nnn>` capture. Ids are immutable once referenced.
- Evidence token: `CAP-014@02:31` (capture id + mm:ss or frame label). A list of tokens is `evidence: [..]`.
- Fidelity: `exact` (match layout, art silhouette, numbers within `tolerance`), `faithful` (same behaviour/feel, own art), `free` (our design, within the brief). Default per file in front-matter, overridable per feature.
- Priority: `P0` = needed for the 3-minute core loop and the first purchase; `P1` = needed for a complete game (retention, secondary shops, bots); `P2` = polish/nice-to-have, dropped first if the day runs out.
- Number provenance: `observed` (seen on screen, with CAP), `estimated` (derived from timing), `derived` (formula from other numbers), `free`. `tolerance_pct` defaults to 15 for observed, 30 for estimated.
- Acceptance criteria are checkable sentences with a verifier tag: `[play]` PlayMode script, `[shot]` screenshot compare, `[edit]` EditMode test, `[inspect]` Editor inspection, `[sim]` balance simulation. A feature without at least one criterion fails lint.
- Unknown values: write `?` plus an entry in `## Open questions`; the linter converts these to blocking questions for P0, to assumptions for P1/P2.

### 1.3 Front-matter envelope and per-type schemas
Envelope (every system file):
```yaml
id: S-01-character
type: character            # character|camera|input|world|interactable|economy|shop|inventory|pets|quests|audio|vfx|monetization|retention|tutorial|localization|bots|minigame
title: Player character
priority: P0
fidelity: faithful
evidence: [CAP-003@00:12, CAP-004@00:40]
depends_on: [S-03-input]
recipe: roblox-character-camera      # optional hint: existing skill/recipe the task generator must load
features:                            # each feature is one orchestrator unit
  - id: F-01.1
    name: Walk/run/jump
    priority: P0
    fidelity: faithful
    acceptance:
      - "[play] character reaches the first platform in <= 3 jumps from spawn"
      - "[edit] jump apex between 1.8 and 2.2 m"
```
Per-type bodies (only the type-specific keys shown; `?` = must be filled or listed as open question):
```yaml
# type: character
rig: humanoid-r6|humanoid-r15|custom      # cosmetic skin swaps must work on this rig
speed_mps: 6.0   jump_height_m: 2.0   gravity_scale: 1.0   air_control: high|low
size_m: {height: 1.7, radius: 0.3}
states: [idle, run, jump, fall, land, ragdoll, dead, carry]     # animation + FSM states required
health: {max: 100, regen_per_s: 0, respawn: checkpoint|spawn}
death_causes: [fall_below_y, kill_brick, enemy]                 # each becomes an interactable or hazard task
camera_target_offset_m: [0, 1.5, 0]
```
```yaml
# type: camera
mode: third_person_orbit|top_down|side|fixed
distance_m: {default: 9, min: 4, max: 14}   fov: {default: 50}
orbit: {pitch_deg: [-10, 60], sensitivity: 0.15, invert_y: false}
zoom: pinch|none        collision: true       follow_damping: 0.0
cinematics: [intro_pan, zone_banner_shake]    # optional
```
```yaml
# type: input
scheme: {move: virtual_joystick_left, look: drag_right_half, buttons: [jump, interact, attack]}
joystick: {region: "left 0.35w x 0.6h", type: floating|fixed, deadzone: 0.1}
contextual_slots: [{slot: A, states: [Attack, Drop]}]          # shared-slot buttons (feedback-notes HUD rules)
keyboard_mouse: true     gamepad: false
```
```yaml
# type: world
zones:
  - id: Z1  name: "Grass Base"  index: 0
    unlock: {kind: free}                       # free|currency|level|rebirth|quest
    size_m: [60, 60]   floors: 10              # towers: floors / height
    theme: {skybox: day, fog: match_sky, palette: [..], landmark: "bridge"}
    spawn: [0, 1, 0]   checkpoints: 5
    banner: {title: "Grass Base", subtitle: "Recommended: 0 coins", show_on_enter: true}
    hazards: [kill_brick, moving_platform, spinner]
    density: {platforms: 40, pickups: 25}      # budgets the world builder must hit
size_budget: {renderers_max: 400, materials: 1}  # catalog 11 material policy
streaming: single_scene|per_zone_scene|culling_zones
safe_zones: [home]
```
```yaml
# type: interactable      (pickups, doors, boards, portals, checkpoints, hazards, buttons)
kinds:
  - id: coin       trigger: touch  effect: {currency: coins, amount: 1}  respawn_s: 0    feedback: [sfx_coin, spread_to_hud]
  - id: checkpoint trigger: touch  effect: {set_respawn: true}            feedback: [flag_wave, toast "Checkpoint!"]
  - id: kill_brick trigger: touch  effect: {kill: true}
  - id: teleporter trigger: touch  effect: {goto_zone: Z2, requires: {key: red}}
placement_rule: "coins every 4-6 m along the path"       # world builder instruction
```
```yaml
# type: economy
currencies:
  - {id: coins, display: "Coins", icon: A-021, start: 0, sources: [coin, floor_bonus, ad_reward], sinks: [skin_shop], cap: null}
  - {id: gems,  display: "Gems",  icon: A-022, start: 0, sources: [iap, daily, boss], sinks: [premium_skins, revive]}
formula: {income: "floor^1.35 * 3", price_curve: "base * 1.6^(tier)", target_time_to_buy_s: {tier1: 60, tier5: 600}}
tables: [economy/prices.csv, economy/rewards.csv]
balance_targets: {first_purchase_s: 90, session_income_min: 5-15, d1_progress: "zone 2"}   # drives the balancer
```
```yaml
# type: shop            (skin shop, pickaxe/tool shop, boost shop, IAP store)
pattern: skin-shop            # ui-pattern-library pattern id, or custom
tabs: [Shop, Avatar]
catalog_table: economy/prices.csv#skins
item_states: [locked, owned, selected, equipped]
buy_rules: {insufficient: "price turns red, no state change", double_tap: "single purchase"}
preview: 2d_image|3d_rig|none
ui: UI-10-skin-shop
persists: Data_Skins
```
```yaml
# type: inventory       (tools, hotbar, backpack, pets-carried)
slots: {hotbar: 4, backpack: 20}   stacking: false
item_kinds: [tool, consumable, cosmetic]
equip_rules: "one tool active; pick-up button near item; Drop replaces Attack while carrying"
capacity_full: "show toast 'Backpack full', item stays"
```
```yaml
# type: pets
catalog: economy/prices.csv#pets    rarities: [common, rare, epic, legendary]  # each: color token + FX tier
acquire: [egg_hatch, shop]   carry: {max: 1, speed_mult: 0.9}   follow: {distance_m: 2, behaviour: trail}
income: {formula: "rarity_mult * kg * 0.2 per s", credits_to: wallet}
equip_slots: 3    ui: UI-14-pets    fx: {obtain: confetti, rare_reveal: beam}
```
```yaml
# type: quests
list: [{id: Q1, text: "Reach floor 10", trigger: {event: floor_reached, value: 10}, reward: {coins: 200}, order: 1, repeat: false}]
tracker_ui: UI-00-hud#quest_tracker    arrow_pointer: true
```
```yaml
# type: audio
bgm: [{id: bgm_main, scope: global, evidence: CAP-020@00:00, source: own|free-pack|silence}]
sfx: [{id: sfx_coin, event: coin_collected, volume: 0.8, pitch_var: 0.05}, {id: sfx_buy, event: purchase_ok}]
rules: {ui_buttons: AudioButtonSfx, mute_on_ad: true, ducking: false}
```
```yaml
# type: vfx
effects:
  - {id: fx_checkpoint, trigger: checkpoint_reached, kind: particle|trail|shake|flash, duration_s: 0.8, budget_particles: 40, pooled: true, fidelity: faithful}
  - {id: fx_coin_spread, trigger: reward_to_hud, kind: ui_spread, count: 8}
shader_policy: "procedural, no textures, SRP Batcher compatible"
```
```yaml
# type: monetization
ads: {rewarded: [{id: ad_revive, placement: death_popup, reward: revive}, {id: ad_double, placement: floor_bonus, reward: "x2 coins"}],
      interstitial: {every_n_deaths: 4, min_interval_s: 120}, banner: {position: bottom, in: [hud]}}
iap: [{id: gems_100, price_usd: 0.99, grants: {gems: 100}}, {id: remove_ads, price_usd: 3.99, type: non_consumable}]
passes: [{id: vip, perks: [coins_x2, free_revive]}]
consent: {gdpr_flow: true, att: true}     sdk_stub: mocked   # real keys per app later
rule: "Ads/IAP optional value, never a paywall"
```
```yaml
# type: retention
daily_reward: {days: 7, rewards: [..], reset: "local midnight", ui: UI-12-daily}
offline_income: false   streaks: false   events: []   push: false   rate_us: {after_floor: 15}
notifications: {badge_on_claimable: true}
```
```yaml
# type: tutorial
steps:
  - {id: T1, trigger: first_spawn, text: "Drag to move", highlight: joystick, advance: moved_3m, forced: true, evidence: CAP-002@00:08}
  - {id: T2, trigger: coins_ge_50, text: "Open the shop", highlight: btn_shop, advance: shop_opened, forced: false}
skip_allowed: true    persist: Data_Tutorial    arrow_to_target: true
```
```yaml
# type: localization
default_locale: en   locales: [en, vi]   keys_source: glossary.md
rules: {numbers: abbreviated "1.2K", plural: none, font: project_text_solution, rtl: false}
string_table: assets/strings.csv     # key,en,vi,context,max_chars
```
```yaml
# type: bots   (other-player simulation)    # optional
count: {min: 4, max: 8}   tiers: [weak, vip]   behaviour_ref: "steal-an-egg canon"   re_roll_strength_s: 120
```
`minigame` type reuses catalog 06 registration chain (`Minigame_Type`, selection asset, scene master).

### 1.4 UI screen schema with layout contract (this is what stops "looks different" and overlap)
```yaml
id: UI-10-skin-shop
type: ui_screen
kind: popup_fullscreen|popup_modal|hud|world_board|toast|banner
fidelity: exact
pattern: ui-pattern-library/skin-shop          # builder to use; else "custom"
opened_by: [btn_shop@UI-00-hud, event:shop_requested]
closes_on: [btn_back, esc, backdrop_if_modal]
reference_canvas: {w: 1080, h: 1920, match: 0.5}   # capture resolution, for scaling the numbers below
captures: [CAP-031@00:00, CAP-032@00:05]            # full-screen shots, one per state
elements:                                           # layout contract: one row per node, numbered
  - {n: 1, name: BtnBack,  anchor: top-left,   pos: [92, -87],  size: [179, 161], sprite: A-040, nine_slice: false, text: null, behaviour: close}
  - {n: 2, name: Tabs_Main, anchor: top-center, pos: [0, -200], size: [509, 92],  children: [BtnShop, BtnCustom]}
  - {n: 3, name: ItemList, anchor: stretch-bottom, rect: {top: 958, bottom: 223}, kind: scroll_grid, cell: {size: [250, 300], columns: 3, spacing: 16}, cell_ref: UI-10#cell}
  - {n: 4, name: BtnBuy, anchor: bottom-center, pos: [0, 110], size: [811, 141], text: {key: ui.buy, auto_size: true}, price_badge: {icon: A-021}, states: {unaffordable: red}}
states: [default, item_locked, item_owned, item_selected, item_equipped, empty_catalog]
cell: {states: [locked, owned, selected, equipped], parts: [icon, name, price, tick, equipped_mark]}
animation: {open: {kind: scale_outback, from: 0.3, t: 0.1}, press: {scale: 0.9, t: 0.1}}
overlap_rules: ["no element rect overlaps another except parent/child", "bottom 200 px reserved for banner on HUD"]
checks: [shot_at_9x16, shot_at_9x20, shot_at_3x4, raycast_only_on_interactive, no_missing_sprite]
```
Notes: `pos`/`size` in reference-canvas pixels (human can read them from a screenshot with a ruler tool or the intake skill extracts them from the capture); builder converts to anchors. HUD files (`UI-00-hud.md`) carry the zone map: every element with `zone: top-left|top-center|top-right|left-mid|right-mid|bottom-left|bottom-center|bottom-right` so the overlap check is mechanical (`mobile-hud-layout` supplies defaults, reference wins).

### 1.5 Economy tables (script-readable)
```csv
# economy/prices.csv#skins
id,name,rarity,currency,price,unlock,evidence,order
skin_01,Classic,common,coins,0,free,CAP-031@00:02,1
skin_02,Ninja,rare,coins,500,free,CAP-031@00:04,2
skin_09,Golden,legendary,gems,150,iap_or_ad,CAP-033@00:12,9
```
`drops.csv` (source,item,weight,pity), `rewards.csv` (event,currency,amount,formula), `timers.csv` (id,seconds,real|game_time), `curves.md` (named formulas used by the balancer, each with 3 sample points observed).

### 1.6 Assets list and reference captures
`assets.csv` row example: `A-021,icon,coin_icon,ref-project,knife-tower:Assets/_Game/.../icon_coin.png,UI-00;E-coins,internal`. `source` decides the task: `ref-project` -> `reference-port` + `asset-transfer-closure`; `generate` -> procedural generator with the material policy; `own` -> import; `buy` -> blocked until human supplies it. `captures/index.md` is the evidence ledger the linter resolves tokens against.

---------------------------------------------------------------------------------------------------
## 2. GDD intake skill (`gdd-intake`): from video/screens/play-notes to a lint-clean GDD

Goal: a human can finish a P0-complete GDD in 2-4 hours of play + notes, with the agent doing the transcription and structuring.

### 2.1 Workflow
1. Scaffold: copy templates into `gdd/`, create `00-index.md` with game name, genre (`roblox-genre-patterns`), orientation, references table (the current `clone-plan` References table).
2. Evidence ingest (human supplies; agent processes). Extends `gameplay-video-analysis`:
   - Videos: with approval, download to a new empty dir, `ffmpeg fps=1/3` + scene-change frames, contact sheets; assign `CAP-nnn` ids and write `captures/index.md` rows. Transcript/subtitles if available.
   - Screens: human drops PNG/JPG named `<screen>-<state>.png`; agent reads each as image and transcribes all text/numbers (`spec-pdf-extract` method for PDFs: open EVERY image).
   - Play notes: human fills the existing observation sheet; intake maps rows into schemas.
3. Draft pass (agent): create one system/UI/economy file per detected system with `?` for unknowns, each field tagged with evidence. Never invent a number: unseen = `?`.
4. Interview pass: agent emits `_generated/questions.md` (max 4 questions per batch, each with a recommended default) from the checklist (2.2) and the lint report. Human answers in chat or edits the file.
5. Numbers pass: tabulate prices/timers/curves; fit formulas (3+ points per curve) and write `curves.md`; flag outliers; `balance_targets` computed from timeline.
6. UI measure pass: for each screen capture, extract the layout contract (positions/sizes in reference-canvas px). Where precision is impossible mark `measure: approx` and fidelity drops to `faithful` unless the human confirms.
7. Reference match: `reference-index` queries per system/UI/asset (`recipe` + `source` fields prefilled with real paths). Mark `reuse: port|adapt|new`.
8. Lint (2.3) loop until zero blockers; then freeze: write `gdd/_generated/gdd.json` and compute a content hash (`gdd_hash`) the orchestrator records.
9. Human sign-off: one short summary (systems, P0/P1/P2 counts, open assumptions, estimated hours). The only intake checkpoint that is mandatory.

### 2.2 Question checklist (agent asks only what remains `?` after drafting; batched, default recommended)
Core loop: one-sentence loop; what ends a run; win/lose; what resets (rebirth/checkpoint)? Character: speed/jump/size vs reference; ragdoll, health? Camera: orbit/zoom/fov. Input: joystick region, buttons set, contextual swaps. World: zone count, unlock gates, size, hazards, spawn/checkpoints, safe zones. Economy: currencies, sources, sinks, first purchase time, price curve 3 points, caps. Shops: tabs, item counts, rarities, currencies per item, preview type. Inventory/tools: slots, equip rules, full-state. Pets/skins: acquisition paths, rarity colors, income. Progression: level/xp/rebirth, FTUE unlocks. Quests/tutorial: steps, forced vs skippable, pointers. Monetization: ad placements, IAP list, passes, VIP, consent. Retention: daily, streak, offline, rate-us. Audio: bgm/sfx per event, silence acceptable? VFX: per event, budget. Localization: languages, text limits. Out of scope: bots, multiplayer (no server: local only). Platform: orientation, min device tier. Legal: any asset that must be replaced (`clone-ip-safety`).

### 2.3 Completeness linter (`gdd_lint.py`, read-only, runs in seconds, output `_generated/lint-report.md` + exit code)
Severity: BLOCK stops the pipeline; WARN becomes a recorded assumption; INFO is a hint.
| Rule | Fails (BLOCK unless noted) |
|---|---|
| L001 schema | front-matter missing/invalid YAML, unknown `type`, missing envelope keys |
| L002 ids | duplicate id; broken `depends_on`/`opened_by`/`used_by` reference; dependency cycle |
| L003 evidence | any P0 feature with `fidelity: exact|faithful` and empty `evidence`; any token not found in `captures/index.md` (WARN for P1/P2) |
| L004 acceptance | feature without a verifier-tagged criterion; P0 feature without a `[play]` or `[edit]` criterion |
| L005 unknowns | any `?` in a P0 file (BLOCK), P1/P2 (WARN -> assumption with default) |
| L006 numbers | economy currency with no source or no sink; price table missing first-purchase row; `observed` number without evidence; curve with < 3 sample points |
| L007 reachability | every item/zone/skin has an unlock path; every currency spendable and earnable; first purchase affordable within `balance_targets.first_purchase_s` (formula check) |
| L008 ui contract | screen without `captures`, `elements` rows missing anchor/size, overlapping rects (computed), HUD element without `zone`, no `states`, text without localization key |
| L009 assets | referenced `A-` id missing from `assets.csv`; `source: buy` unresolved; `ref-project` path missing (checked with the reference index); asset without license/provenance field |
| L010 orphan | system with no UI/feature referencing it, UI screen no system opens, currency never shown in HUD |
| L011 budget | P0 effort estimate (from the task generator dry run) > 60% of the day budget (WARN) or > 100% (BLOCK: cut scope) |
| L012 coverage | required P0 types missing: character, camera, input, world, economy, one HUD, one reachable purchase, golden-path.md |
| L013 monetization | ad placement without a reward/target UI; IAP without grant; no consent flow when ads exist (WARN) |
| L014 fidelity | `exact` UI without a full-screen capture per state (BLOCK); `exact` sprite assets sourced `generate` (WARN, must justify) |
| L015 stale | `gdd_hash` differs from last orchestrator run -> INFO "GDD changed", triggers re-plan of impacted tasks only |
Lint output also contains a dry-run summary: counts by type/priority, estimated hours by phase, assumptions list.

---------------------------------------------------------------------------------------------------
## 3. Orchestrator design (`clone-orchestrator` skill + `orchestrator.py` helper + subagent roles)

### 3.1 Roles
Producer (main agent, owns state + gates), Designer (spec-then-plan per system, balance), Dev (code + data chain), Builder (Editor wiring via Unity MCP; the single Editor writer), UI agent (`ui-clone` family), Tester (PlayMode scripts + shot compare + perf), Reviewer (diff vs spec acceptance). Roles are prompts + skill lists, not new frameworks. Subagents get exactly the task text, files, skills, acceptance (as `spec-then-plan` and `dispatching-parallel-agents` prescribe) and return <= 200 words.

### 3.2 Phases and gates
Time/token numbers are per a 16 h wall-clock day (see 3.6). Gate = artifact + automated check; `H` = human checkpoint (3.9).
| Ph | Name | What happens | Skills loaded | Gate (all must pass) | Human |
|---|---|---|---|---|---|
| 0 | Spec | lint-clean GDD frozen; generate `docs/clone-plan.md` + task graph; `spec-then-plan` per P0 system (short specs, thunder-break-egg format) | gdd-intake, spec-then-plan, game-clone-recon, clone-ip-safety | lint 0 BLOCK; specs exist for every P0 system; task graph acyclic; estimate <= budget | H1 sign-off (summary only) |
| 1 | Foundation | project bootstrap, MCP connected, mobile URP, folders/asmdefs, framework version map, singleton/boot, cheats menu, context map, build-gate + guard scripts | unity-project-bootstrap, unity-mcp-workflow, project-context-map, config-driven-feature, unity-code-templates, debug-cheats-menu | compiles, Console clean, boot scene plays, `PROJECT-MAP.md` written | - |
| 2 | Core loop | character, camera, input, world greybox of zone 1, checkpoints, pickups, economy first loop (earn) | roblox-character-camera, mobile-input-controls, zone-level-design, clone-feature-recipes, economy-progression-design | golden-path steps 1..N pass in PlayMode script; feel numbers within tolerance | H2: play 3 min, react (taste: feel) |
| 3 | UI | HUD, popups, shop screens from layout contracts, currency spread, localization keys | ui-pattern-library, ui-clone, unity-ui, mobile-hud-layout, ui-style-rules, currency-spread-fx | shot compare at 3 ratios under threshold, overlap check 0, no missing sprites/scripts | H3: side-by-side screenshots (taste: look) |
| 4 | Content | remaining zones, skins/items/pets from tables, bots, audio, VFX, tutorial, retention | zone-level-design, npc-bots-and-enemies, game-audio-system, game-feel-polish, world-batching-culling, reference-port, asset-transfer-closure | every catalog row present and reachable (data-driven audit), all `A-` assets resolved, provenance file complete | - |
| 5 | Monetization | ads layer (mocked), IAP stubs, consent, passes, rewarded revive/double flows | monetization-integration, ads-popup-flow, unity-iap-port | each GDD placement fires in PlayMode with mock SDK, never blocks play when ad fails | - |
| 6 | QA/balance | wiring audit, full-game simulation, auto-balance loop, perf, log triage, regression of all earlier gates | done-means-wired, unity-qa-playtest, playmode-script-testing, mobile-perf-audit, unity-log-triage, economy-progression-design | all acceptance criteria green; balance targets met (sim); perf budget in Editor Mobile tier; Console clean | H4: final play + sign-off |
| 7 | Build | Android build (iOS if requested), release checklist | mobile-build-release | build succeeds; build gate script passes; APK size/permissions report | H5: device install only if tester has device |

### 3.3 Task-graph generator (`gen_task_graph.py`; deterministic, no LLM needed for 90%)
Input `gdd.json`. Output `task-graph.json` (and a human `task-graph.md` table). Algorithm:
1. For each feature, instantiate the task template of its system type (below). A template yields a chain: `data -> logic -> asset/config -> wiring -> verify`.
2. Add cross-cutting tasks once per game: bootstrap, boot scene, cheats, economy tables -> config assets (`Generate All Configs` style idempotent tool), localization table, golden-path PlayMode script, asset provenance, perf pass, build.
3. Resolve `depends_on` between systems into task edges; add implicit edges: Editor tasks on the same scene/prefab are serialized (edge by claim key, 3.5).
4. Topological sort; assign `phase` from template; compute `group` (parallelizable set = tasks with equal depth and disjoint `claims`); compute critical path hours.
5. Priority cut: if estimate > budget, drop P2 then P1 tasks (producer asks only if P0 alone exceeds the budget).
6. Emit `state.json` seed with all tasks `pending`.
Task template per type (abbreviated):
| GDD type | Tasks generated (phase) | Skills | Verify |
|---|---|---|---|
| character | T-data(Data+Config) , T-controller (KCC+states), T-anim wiring, T-skins hook (2,4) | roblox-character-camera, config-driven-feature | [edit] feel numbers; [play] move/jump path |
| camera/input | T-camera, T-input+joystick (2) | mobile-input-controls | [play] no overlap, joystick region |
| world | T-zone-greybox per zone, T-hazards, T-checkpoints, T-batching/culling per zone (2,4) | zone-level-design, world-batching-culling | [play] path reachable; renderers/materials within budget |
| interactable | T-registry-collidable per kind + T-placement (2) | clone-feature-recipes, (collision registry rule) | [edit]/[play] trigger fires once; no `GetComponent` in callback |
| economy | T-tables->configs, T-wallet+events, T-sim harness (2,6) | economy-progression-design | [sim] first purchase time, price curve |
| shop | T-ui-from-pattern, T-logic(buy/equip/persist), T-catalog-fill (3,4) | ui-pattern-library, ui-clone | [shot]+[play] buy/equip/restart persists |
| inventory/pets | T-data, T-logic, T-ui, T-world-view (4) | clone-feature-recipes | [play] pick/drop/full state |
| quests/tutorial | T-state-machine, T-ui-pointer (4) | clone-feature-recipes, unity-ui | [play] full tutorial path |
| audio/vfx | T-audio-factory+events, T-fx-prefab+pool (4) | game-audio-system, game-feel-polish | [inspect] every event has sfx; pooled |
| monetization/retention | T-ads-layer, T-iap-stub, T-flows, T-daily (5) | monetization-integration, ads-popup-flow | [play] mock flows |
| ui_screen | T-build-prefab (idempotent builder), T-bind, T-shot-compare (3) | unity-ui, ui-popup-from-demo, ui-scroll-board | [shot] 3 ratios; overlap 0 |
| localization | T-string-table+runtime lookup (3) | ui-style-rules | [inspect] no hard-coded text |
Task record:
```json
{"id":"T14","feature":"F-06.2","title":"Skin shop logic: buy/equip/persist","phase":3,"skills":["config-driven-feature","unity-code-templates","done-means-wired"],
 "agent":"dev","claims":["code:Logic/Shop/Skin/*","asset:SingletonAssets/Factory_Skins"],"files_touched":["Scripts/Logic/Shop/Skin/Skin_Shop.cs","Scripts/Data/Data_Skins.cs"],
 "depends_on":["T09","T12"],"group":"G3-b","est_h":0.8,"verify":["[edit] SkinShopTests","[play] golden-path step 9"],"status":"pending","attempts":0}
```

### 3.4 Parallelism model (one Editor, many hands)
Hard fact: one Unity Editor instance == one project directory; the Unity MCP controls that one Editor. Therefore:
- Editor lane (serial): everything that mutates scenes, prefabs, ScriptableObject assets, import settings, ProjectSettings, plus compile/Play/screenshot tests. One Builder agent owns this lane; it executes a queue.
- File lane (parallel): C# code, EditMode tests, editor-tool scripts, CSV/config tables, GDD-derived data, docs, python scripts. Run in subagents with `isolation: worktree` (own git worktree branch `gen/<task-id>`), no Unity open in the worktree. The producer merges worktrees into the main working tree between Editor tasks (rebase, never reset), then Unity compiles once for the batch (`unity-fast-iteration`).
- Claims: each task lists `claims` (`scene:`, `prefab:`, `asset:`, `code:`); `workspace_guard.py claim/check` per `multi-agent-coexistence`; two tasks with an overlapping claim never run in one group. Re-read a file immediately before editing it; no whole-file rewrites; shared docs append-only.
- Max concurrency: 4 file-lane subagents + 1 Editor lane (more only raises merge cost and token burn).
- Group types: `G<phase>-<letter>`; a group closes when all members are merged and one compile + Console read is clean. A group failure is bisected by task (revert only that task's commit-less patch via worktree discard, never `git reset`).
- Idempotent editor tools only (`editor-tool-authoring`): every generator removes its own previous output, guards loops, saves the scene after each stage, one stage per MCP call (30 GB hang lesson).

### 3.5 State file (resume after crash or context compaction): `docs/orchestrator/state.json` + `log.md`
```json
{
  "schema": 1, "game": "Sky Climb", "gdd_hash": "9f3c...", "started": "2026-10-16T08:00:00+07:00",
  "phase": 3, "gate": {"G0":"pass","G1":"pass","G2":"pass","G3":"open"},
  "budget": {"day_h": 16, "spent_h": 6.2, "tokens_spent": 2.9e6, "tokens_cap": 8e6},
  "editor": {"project": "C:/...", "scene": "Game.unity", "mcp": "ivanmurzak-connected", "lock_owner": "builder", "last_compile_ok": true},
  "tasks": {"T09": {"status": "done", "evidence": ["Console clean 12:04", "PlayMode golden step 6 pass"], "commit_free_ref": "worktree gen/T09 merged 12:10"},
            "T14": {"status": "in_progress", "agent": "dev-3", "started": "12:15", "attempts": 1, "last_note": "tests red: double tap"}},
  "assumptions": ["A1: coin spawn every 5 m (GDD said 4-6)"],
  "human_pending": [], "blockers": [],
  "next_actions": ["merge T14", "queue T15 wiring in editor lane"]
}
```
Rules: written after every task transition (atomic: write temp + rename); `log.md` is append-only one line per event with time + task + verdict. On session start the producer reads, in order: `state.json`, last 30 lines of `log.md`, `docs/feedback-notes.md`, `docs/decisions` tail, `PROJECT-MAP.md`, `git status`, then reconciles reality (task marked done but file missing -> reopen; in_progress with no live agent -> `attempts++` and re-dispatch). Stale-copy protection: the state file records the file hashes of claimed files at claim time; check before write. Compaction: durable facts are already in files; the producer prompt after compaction is "read state, continue next_action".

### 3.6 Budget per phase (starting guesses; recalibrate after the pilot, section 6.4 of this plan)
Day = 16 h wall-clock with 4 parallel file-lane agents + 1 Editor lane; token cap about 8 M including subagents (heavy cost is Editor/PlayMode loops and screenshots, so cache indexes, use scale 0.4 screenshots, `token-efficient-workflow`).
| Phase | Wall h | Tokens | Notes |
|---|---|---|---|
| 0 Spec | 0.75 | 0.4 M | specs short; generated plan from graph |
| 1 Foundation | 1.25 | 0.5 M | mostly templates/scripts |
| 2 Core loop | 3.0 | 1.5 M | feel iteration is the risk; cap 2 tuning rounds before H2 |
| 3 UI | 3.0 | 1.8 M | screenshots + compares; builder reuse of patterns |
| 4 Content | 2.5 | 1.3 M | data-driven filling, mostly generators |
| 5 Monetization | 1.0 | 0.5 M | recipes + mock |
| 6 QA/balance | 3.0 | 1.5 M | sim + regression |
| 7 Build | 0.75 | 0.2 M | |
| Slack | 0.75 | 0.3 M | reserve |
Per-task limits: 3 attempts, then `blocked` + simplest fallback (drop to `free` fidelity or cut P2) + log; per-task time cap = 2x estimate. Phase overrun > 30% triggers scope cut (P2 first) automatically, announced in the report.

### 3.7 Definition of done
Per task: code compiled, Console clean of new warnings/errors, asset chain complete (data -> config -> factory -> prefab/scene wiring -> installer run), serialized refs non-null (inspect), acceptance criteria run with evidence recorded in `state.json`, no TODO/placeholder, docs/handoff line appended. Per feature: all its criteria green on a fresh save AND after restart (persistence). Per game: golden-path script passes from the real entry flow at `timeScale = 1`; every GDD feature has `status: done` or an explained `cut`; `asset-provenance.md` complete; balance sim in target bands; shots match at 3 aspect ratios; Console clean; build gate passes. A feature is never "done" with only scripts (`done-means-wired`).

### 3.8 Verification stack (what replaces "looks right")
- Data audit: GDD tables vs config assets (row counts, ids, prices) via an editor script; any mismatch fails the gate.
- Wiring audit: scan for missing scripts/null serialized refs on source prefabs and scene instances; every `opened_by` link in UI contracts has a live opener.
- PlayMode script (`qa/golden-path.md` -> generated test): drives input/events, asserts state (wallet, owned skin, zone), saves screenshots at fixed points.
- Shot compare: reference capture vs our screenshot at the same canvas/ratio; automated diff (SSIM/edge map) gives a score and a diff image; agent reads the diff and fixes; threshold per fidelity (exact strict, faithful lenient, free none).
- Layout validator: rect overlap check on built prefab; text overflow check; raycast-target audit.
- Balance sim: headless loop using the economy formulas (`EggBalanceFormula` pattern: one deterministic file) -> time-to-buy table vs `balance_targets`; auto-tune loop with stop criteria (3 iterations or targets within tolerance).

### 3.9 Human checkpoints (only where taste matters; each is a 5-minute action, not a blocker for unrelated work)
| H | When | Human does | Pipeline behaviour while waiting |
|---|---|---|---|
| H1 | after lint-clean GDD | read the one-page summary + assumptions, approve scope | stop (nothing built yet) |
| H2 | gate G2 | play 3 min, say "feel ok / faster / floatier" | continue Phase 3 UI in parallel on a snapshot; apply feedback as tuning tasks |
| H3 | gate G3 | compare screenshots (diff pairs) and approve or mark deltas | continue Phase 4 data-only tasks (no UI changes) |
| H4 | gate G6 | final play + decide balance feel | prepare build |
| H5 | optional | install on device | - |
Everything else (naming, architecture, tuning inside tolerance, ordering) is decided by agents and logged to `decisions.md`. Feedback received at any H is appended to `docs/feedback-notes.md` immediately (existing rule) and may add tasks.

---------------------------------------------------------------------------------------------------
## 4. Worked example: "Sky Climb" (tower climb with a skin shop), invented GDD, 1-day plan

### 4.1 The GDD (shortened; real files would carry full front-matter)
`gdd/00-index.md`
```yaml
game: Sky Climb       genre: obby-tower-climb     orientation: portrait      reference_game: "<roblox game>"   platform: android-low-mid
references: [{name: knife-tower, path: C:/Unity/GitProject/knife-tower/..., index: indexes/knife-tower.json, source_of: [tower, checkpoint, revive, skin-shop-ui]}]
loop: "Climb floors, collect coins at checkpoints, buy skins, climb higher"
systems: [S-01-character, S-02-camera, S-03-input, S-04-world, S-05-interactables, S-06-economy, S-07-skin-shop, S-08-monetization, S-09-tutorial, S-10-audio, S-11-vfx, S-12-retention]
priorities: {P0: [S-01..S-07], P1: [S-08, S-09, S-10], P2: [S-11, S-12]}
fidelity_default: faithful     ui_default: exact     locales: [en]     local_only: true
```
`S-04-world` (excerpt): 3 zones (Meadow floors 1-12, Cloud 13-24, Sun 25-36), 3 checkpoints per zone, hazards kill_brick + moving_platform + spinner, budgets `renderers_max: 350, materials: 1`, banner on zone enter. `S-06-economy`: coins (floor bonus `floor*3`, pickup 1) and gems (ad/IAP), `first_purchase_s: 90`, skins 12 (7 coins 0-4000, 3 gems, 2 ad-unlock). `S-07-skin-shop`: `pattern: skin-shop`, tabs [Shop], preview `2d_image`, UI-10 `exact` with 4 states. `S-08`: rewarded revive on death, rewarded x2 floor bonus, interstitial every 4 deaths, IAP gems_100. `S-09` 3 steps. UI files: UI-00-hud (coins/gems top-right, floor counter top-center, jump + interact bottom-right, joystick left, shop button right-mid), UI-10-skin-shop, UI-11-revive-popup, UI-12-settings. Golden path: spawn -> move -> jump -> checkpoint -> floor 5 -> coins >= 500 -> open shop -> buy `skin_02` -> equip -> restart app -> equipped persists -> die -> revive via mock ad.
Lint result for this GDD: 0 BLOCK, 3 WARN (S-10 BGM source undecided -> assumption "silence + one free-pack track"; UI-12 element 4 size approx; skin_11 price estimated), estimate 14.6 h critical path 12.3 h -> inside the 16 h day.

### 4.2 Generated task graph (Phase / task / skills / agent / main files / verify / group / est h)
Agent codes: P = producer, D = dev (file lane, worktree), B = builder (Editor lane), U = UI agent, T = tester. Est h = agent wall-clock, not including waiting.
| Id | Ph | Task (feature) | Skills | Ag | Files / claims | Verify | Grp | h |
|---|---|---|---|---|---|---|---|---|
| T01 | 0 | Lint + freeze GDD, generate clone-plan, graph | gdd-intake, game-clone-recon | P | gdd/_generated/* | lint 0 BLOCK | G0 | 0.3 |
| T02 | 0 | Specs for S-01..S-07 (short, thunder-break-egg format) | spec-then-plan | D x3 | docs/specs/* | self-review checklist | G0 | 0.5 |
| T03 | 0 | Asset provenance + reference index build | reference-index, clone-ip-safety, asset-transfer-closure | D | docs/asset-provenance.md, indexes/ | all `ref-project` paths resolve | G0 | 0.2 |
| T04 | 1 | Project bootstrap: mobile URP, folders, asmdefs, framework map, MCP | unity-project-bootstrap, unity-mcp-workflow | B | ProjectSettings, Assets/_Game/* | compile, Console clean | G1-a | 0.7 |
| T05 | 1 | Boot scene + Data/Factory scaffolding + cheats menu | config-driven-feature, unity-code-templates, debug-cheats-menu | D | Scripts/Core, Data, Factory | EditMode boot test | G1-b | 0.5 |
| T06 | 1 | Project map + build-gate scripts + guard/claims init | project-context-map, multi-agent-coexistence | D | docs/PROJECT-MAP.md | map paths exist | G1-b | 0.3 |
| T07 | 2 | Character controller + states + anim wiring | roblox-character-camera, done-means-wired | D+B | Logic/Character/*, prefab Character | [edit] speed/jump bands; [play] reach platform | G2-a | 1.2 |
| T08 | 2 | Camera orbit + input joystick/jump | roblox-character-camera, mobile-input-controls | D | Logic/Camera, Input | [play] joystick region; no overlap | G2-a | 0.8 |
| T09 | 2 | Interactables: collision registry, coin, checkpoint, kill brick, moving platform, spinner | clone-feature-recipes | D | Logic/Interact/* | [edit] once-only trigger; no GetComponent in callbacks | G2-a | 1.0 |
| T10 | 2 | Economy data: tables -> config assets + wallet + events | economy-progression-design, config-driven-feature | D | Configs/Economy, Data_Wallet | [edit] wallet/events | G2-b | 0.7 |
| T11 | 2 | Zone 1 greybox (12 floors) + checkpoints + hazards placement tool | zone-level-design, world-batching-culling | B | scene Game, prefabs Zone1 | [play] path reachable, renderers <= budget | G2-c | 1.3 |
| T12 | 2 | Respawn/fall/death loop + floor counter + floor bonus | clone-feature-recipes | D+B | Logic/Run/* | golden steps 1-6 | G2-c | 0.8 |
| T13 | 2 | Gate G2: golden path steps 1-6 PlayMode script + H2 | playmode-script-testing, unity-qa-playtest | T | Tests/PlayMode | script passes | G2-z | 0.6 |
| T14 | 3 | HUD from UI-00 contract (zones, safe area, counters) | mobile-hud-layout, unity-ui, ui-clone | U+B | prefab GUI, UI-00 | [shot] 3 ratios; overlap 0 | G3-a | 1.2 |
| T15 | 3 | Skin shop UI from pattern (UI-10 exact) | ui-pattern-library, ui-popup-from-demo, ui-scroll-board | U+B | prefab Popup_SkinShop | [shot] 3 ratios, 4 cell states | G3-b | 1.4 |
| T16 | 3 | Skin shop logic: buy/equip/persist + catalog fill | config-driven-feature, done-means-wired | D | Logic/Shop/Skin, Data_Skins | [edit] insufficient funds unchanged; restart persists | G3-b | 0.8 |
| T17 | 3 | Revive + settings popups, popup manager wiring | unity-ui, ui-style-rules | U+B | Popup_Revive, Popup_Settings | [shot] + [play] open/close/Esc | G3-c | 0.9 |
| T18 | 3 | Currency spread FX + localization table + press feedback | currency-spread-fx, ui-style-rules | D | Logic/UI/* | [play] coin flies to HUD | G3-c | 0.5 |
| T19 | 3 | Gate G3: shot diffs, H3 | unity-qa-playtest | T | qa/shots | diff scores in band | G3-z | 0.5 |
| T20 | 4 | Zones 2-3 greybox + banners + culling zones | zone-level-design, world-batching-culling | B | scene Game | [play] reach floor 36; budget | G4-a | 1.5 |
| T21 | 4 | 12 skins: transfer/generate, avatar icons, factory fill | reference-port, asset-transfer-closure, config-driven-feature | D+B | Configs/Skins, Art/Skins | data audit = prices.csv | G4-b | 1.0 |
| T22 | 4 | Tutorial (3 steps) | clone-feature-recipes | D+B | Logic/Tutorial | [play] full tutorial path | G4-c | 0.6 |
| T23 | 4 | Audio factory + sfx wiring (P1) | game-audio-system | D | Logic/Audio, Configs/Audio | [inspect] each event has sfx | G4-c | 0.5 |
| T24 | 4 | Feel pass + checkpoint/skin VFX pooled (P2) | game-feel-polish | D+B | Logic/Vfx | pooled, budget | G4-d | 0.6 |
| T25 | 5 | Ads layer (mock): rewarded revive/x2, interstitial rule, consent | monetization-integration, ads-popup-flow | D | Logic/Ads | [play] mock flows, ad failure never blocks | G5-a | 0.8 |
| T26 | 5 | IAP stubs + gems_100 + daily reward (P2) | unity-iap-port, clone-feature-recipes | D+B | Logic/Iap, UI-12 | [play] grant once | G5-a | 0.6 |
| T27 | 6 | Wiring audit + data audit + Console triage | done-means-wired, unity-log-triage | T | reports | zero missing refs | G6-a | 0.6 |
| T28 | 6 | Balance sim + auto-tune + full golden path | economy-progression-design, unity-qa-playtest | T+D | Editor/Balance, qa | first purchase 80-100 s, price curve | G6-b | 1.2 |
| T29 | 6 | Perf audit Mobile tier + fix list | mobile-perf-audit, world-batching-culling | T+B | reports | batches/verts within budget | G6-b | 0.8 |
| T30 | 6 | Regression of gates G2/G3 + H4 | playmode-script-testing | T | qa | all green | G6-z | 0.5 |
| T31 | 7 | Android build + release checklist | mobile-build-release | B | Build/* | build ok, gate script | G7 | 0.6 |
Totals: sum of est h = 27.6 agent-hours; with 4 file-lane workers and 1 Editor lane the critical path is about 13.5 h wall-clock (Editor-lane tasks T04, T11, T14/15/17 wiring, T20, T31 serialize); inside a 16 h day with 2.5 h of slack, assuming no more than 15% rework and H2/H3 answered within 20 min. If H responses lag, Phase 4 data tasks and Phase 5 continue (see 3.9).

### 4.3 What an unattended run looks like (timeline)
08:00 T01-T03 -> 08:45 H1 summary -> 09:00 Phase 1 -> 10:15 Phase 2 (T07-T09 parallel in worktrees, T11 in Editor lane) -> 12:30 G2 + H2 -> 13:00 Phase 3 (UI builder tasks serialized, logic in parallel) -> 16:00 H3 -> Phase 4/5 -> 21:00 Phase 6 -> 23:00 build. Wall times are illustrative; budgets are checked, not promised, until the pilot calibrates them.

---------------------------------------------------------------------------------------------------
## 5. Risks and how the pipeline prevents the recorded repeated mistakes

| Mistake (source) | Prevention in this design |
|---|---|
| Looks different from the reference (feedback notes HUD 2026-10-12; "close enough" rejected; `ui-clone` lessons) | `exact` UI needs full-screen capture per state (L014) and a numbered layout contract (1.4); builder from `ui-pattern-library`/reference prefab; automated shot diff at 3 ratios is a gate (3.8); H3 compares diff pairs, not memory; art `source` forces `reference-port` before `generate` |
| Invented visuals/icons where a sister project already has them (N:373) | `assets.csv` source field resolved through `reference-index` at lint (L009); `generate` for `exact` assets warns; `reference-port` mandatory first |
| Unwired features ("can't click", scripts only) | Every task template ends in wiring + verify; DoD requires data->config->factory->prefab chain and non-null refs; wiring audit is a Phase 6 gate; `opened_by` links lint (L010); PlayMode golden path exercises real entry flow |
| UI overlap, wrong anchors, mirrored text, broken 9-slice | HUD `zone` field + computed rect-overlap lint (L008) before build and on the built prefab; `unity-ui` validation at 3 ratios; builders own output (rebuild, never hand-patch); text raycast/overflow checks; sliced sprites flagged `nine_slice` in the contract |
| Lost decisions after context compaction | `decisions.md` + `docs/feedback-notes.md` + `state.json` + append-only `log.md`; resume procedure reads them in fixed order; no decision lives only in chat |
| Stale-copy overwrites between agents / Editor holding old scene | one Editor writer lane; worktrees for file lane; claims + `workspace_guard` snapshot/check; re-read before edit; hash of claimed files in state; after external merge the Editor reloads scene/prefab before save; shared docs append-only |
| Per-object materials / 3767 renderers (catalog 11) | `world.size_budget` (`renderers_max`, `materials`) is an acceptance criterion; world builder bakes by material policy; perf gate at Phase 6; zone tasks include culling |
| Price curve that takes years / flat economy (SKILL-SUITE-PLAN) | L006/L007 reachability + formula checks at lint; balance sim gate with targets; one deterministic formula file; fast-forward is QA only and runs on a clean save |
| QA lies (timeScale 60, polluted saves) | golden path runs at `timeScale = 1` for the gate; sim uses formulas not Play Mode; clean-save fixture before each gate |
| Unity hang / duplicate objects from MCP retries (30 GB) | idempotent guarded generators, one stage per MCP call, save after stage, never `InstantiatePrefab` on nested children; builder queue serializes |
| Work started from memory instead of evidence | no evidence = `?` or `free`; unknowns on P0 block (L005); tasks cite evidence tokens in their text |
| GDD too thin/hand-wavy for agents | linter + dry-run estimate; intake skill drafts and interviews; sign-off H1 shows assumptions list |
| Scope exceeds the day | priority cut (P2 then P1) is automatic with a logged report; budget table per phase; per-task attempt cap |
| Numbers "differ slightly" accidentally become wrong | `tolerance_pct`, `observed/estimated` provenance, balance sim in bands; only deviations beyond tolerance are flagged |
| Hosted-framework mismatches (CodeSketch vs SketchEngine) | foundation task writes the framework version map first; task templates read it; never mass rename |
| IP/asset provenance forgotten | `assets.csv` license column, provenance file generated at Phase 0 and checked at build gate |
| Agents burn tokens exploring | index queries, project map, short specs, <= 200-word subagent reports, scale-0.4 screenshots |
Residual risks (not solved by design alone): real feel parity needs human taste at H2; no device data without hardware; Roblox-specific mechanics with no clear recipe (physics puzzles, complex bots) cost more than estimated; screenshot diff is only as good as capture quality; the pilot may show 1 day is really 1.5 days for a first game (second game faster once recipes exist).

---------------------------------------------------------------------------------------------------
## 6. Build plan for this design (what to implement and test)
1. Write schemas as JSON Schema + templates (`gdd/` scaffold) and `gdd_lint.py` (stdlib + PyYAML optional fallback parser). Unit-test the linter on the Sky Climb example, one broken variant per rule.
2. `gen_task_graph.py` + templates table; dry-run on Sky Climb; compare estimate to the table above.
3. `clone-orchestrator` skill: phases, resume procedure, state schema, claims; `orchestrator.py status|next|mark|resume`.
4. `gdd-intake` skill + capture ingest script (ffmpeg frames + `captures/index.md` generator) and layout-contract extractor from screenshots (assisted, human-confirmable).
5. Pilot on one real small clone; measure per-phase hours/tokens/rework; recalibrate 3.6; fold lessons into the skills and `feedback-notes`.

## Proposed classification
| Item | Class | Proposed name | Notes |
|---|---|---|---|
| GDD folder layout, ids, evidence tokens, fidelity/priority/number-provenance conventions | DATA | `gdd-template/` (scaffold + 00-index template) | the contract between human and agents |
| Per-type front-matter schemas (sections 1.3-1.5) | DATA | `gdd-schemas/*.schema.json` + `gdd-templates/systems/*.md` | one template per type; UI contract template included |
| Intake workflow and question checklist | SKILL | `gdd-intake` | extends `gameplay-video-analysis`, `spec-pdf-extract`, `game-clone-recon`; writes the GDD |
| Completeness linter (L001-L015) with dry-run estimate | TOOL | `gdd_lint.py` | read-only, runs in seconds, produces questions and assumptions |
| Task-graph generator and templates per system type | TOOL + DATA | `gen_task_graph.py` + `task-templates.yaml` | deterministic; emits `task-graph.json`, `task-graph.md` |
| Orchestrator phases, gates, resume procedure, parallel/claims rules, DoD, human checkpoints | SKILL | `clone-orchestrator` (supersedes the manual part of `clone-pipeline`; `clone-pipeline` remains the phase->skills map) | state file schema in 3.5 |
| State/log handling and resume commands | TOOL | `orchestrator.py` (`status|next|mark|resume`) | atomic writes, hash checks |
| Idempotent Editor-lane rules (single writer, worktrees for file lane) | RULE | `editor-lane-single-writer` (AGENTS.md + `multi-agent-coexistence`) | one Editor = one project |
| Verification stack (data audit, wiring audit, golden-path PlayMode generator, shot-diff compare, layout overlap validator, balance sim harness) | TOOL | `qa-kit` (`data_audit`, `wiring_audit`, `golden_path_gen`, `shot_diff.py`, `layout_check`, `balance_sim`) | shot diff and layout check are shared with `ui-clone` |
| Per-phase budgets and scope-cut policy | RECIPE | `day-budget-recipe` (inside `clone-orchestrator/references`) | recalibrated after pilot |
| Reference-canvas to anchor conversion for UI contracts | TOOL | `ui_contract_to_prefab` (extends the pattern builders) | consumes UI front-matter |

Must-haves (in order):
1. `gdd-template` + schemas + evidence/fidelity/priority conventions (without a strict contract nothing downstream is automatable).
2. `gdd_lint.py` with L003/L005/L007/L008/L014 first (evidence, unknowns, reachability, UI contract, exact-UI capture): these stop the costliest repeated mistakes.
3. `clone-orchestrator` skill + `state.json`/`log.md` resume protocol + single-Editor-writer rule.
4. `gen_task_graph.py` with templates for character, world, interactable, economy, shop, ui_screen (the P0 set for obby/tower clones).
5. `qa-kit` minimum: data audit + wiring audit + golden-path PlayMode script + shot diff at 3 ratios (the objective "done" evidence).
6. `gdd-intake` skill with capture ingest and the question checklist (increases the human's authoring speed; can start as a checklist before the tooling exists).
