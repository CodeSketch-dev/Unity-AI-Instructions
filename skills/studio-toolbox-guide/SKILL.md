---
name: studio-toolbox-guide
description: "Use when starting a feature and unsure which studio kit or skill applies: opt-in knowledge map 'when building X, load skill Y' over the prefab kit and existing skills. Not a default load list; genre-neutral first, genre packs optional."
triggers: toolbox, which skill, which kit, skill map, building a feature, load kit, toolbox guide, nen dung skill nao, ban do skill, bo cong cu studio, knife tower style
---

# Studio toolbox guide

Opt-in knowledge map. NOTHING here is a default: read the one row matching the current step, load that skill, drop it when the step ends (`token-efficient-workflow`). Genre-neutral rows come first; genre packs load only when the game's genre needs them. Kit index: `prefab-kit-catalog`.

## 1. When building X, load Y
| Building | Load |
|---|---|
| First-time-user flow, hand pointer, focus hole, ground arrow | `tutorial-focus-notice-hand`, `tutorial-phase-system`, `kit-ui-services` |
| Popup, shop tabs, IAP card, currency bar, reward fly-in, toast | `kit-ui-services`, `ui-always`, `shop-tab-page-checklist`, `currency-spread-fx` |
| Daily login, rating, settings, offline reward | `kit-ui-services`, `recipe-retention-timers`, `rating-prompt-flow`, `settings-pause-offline` |
| Revive / continue offer, results | `kit-ui-services`, `revive-result-flow` |
| Actor/pet/NPC with swappable looks, skin shop | `kit-characters-skins-ai`, `character-skin-system`, `shop-skin-preview` |
| Bots or ambient crowd | `kit-characters-skins-ai`, `bots-as-players`, `bot-brain-waypoints`, `device-tier-policy` |
| Trails, burst FX, pooled floating text | `kit-characters-skins-ai`, `pooled-ranked-fx`, `vfx-budget-rules` |
| New mode/minigame, Home card, mode policy | `kit-minigame-platforms`, `minigame-registration`, `recipe-add-minigame` |
| Hazards, movers, conveyors, bouncers, teleporters | `kit-minigame-platforms`, `platform-kit`, `teleporter-pad`, `collision-registry` |
| Checkpoints, respawn, progress save | `kit-minigame-platforms`, `checkpoint-respawn`, `data-persistence-facts` |
| Level/stage/map, container, stage order | `kit-maps-stages-optimizer`, `map-chunk-prefabs`, `zone-level-design` |
| Scene optimizer, combine, cull, bake | `kit-maps-stages-optimizer`, `scene-optimizer-bake`, `mesh-scene-combiner`, `culling-group-distance` |
| Config SO, Factory, audio, pools, URP tier, fonts, atlases, localization | `kit-assets-config-shaders` plus the skill it names for the sub-area |
| Importing from a reference project | `prefab-kit-catalog`, `asset-transfer-closure`, `reference-port`, `clone-ip-safety` |

## 2. Genre packs (load only if the game is that genre)
- Tower / vertical climber: floors stacked by an editor generator, per-floor fall detector (`kit-maps-stages-optimizer`, section 5).
- Parkour / obby: stage chain, glass bridge, fade tiles, mover platforms (`kit-minigame-platforms`).
- Collector/pets, tycoon, runner: use the neutral rows; each kit recipe lists the genres it fits.
- Casual live-ops: jackpot slot and gacha box (`kit-ui-services` recipe I; always show odds and a pity counter).

## 3. Rules
1. Prefer SketchEngine concepts; check the installed package API before any named type.
2. Kit items are patterns to re-author, not files to copy; run the referrer scan and closure check from `prefab-kit-catalog`.
3. A kit never overrides a house rule: prefabs placed in the scene, UI authored in Edit Mode, gates in `studio-non-negotiables`.
4. No row fits: say "no matching row", use the closest, note it for `studio-self-training`.

## Done-check
Only the rows needed were loaded; the plan names which kit parts were reused and which genre packs were deliberately skipped.
