---
name: prefab-kit-catalog
description: "Use when choosing what to reuse from the studio reference prefab kit: index of kit groups, which kit-* skill to load, top reusable items, import rules (dependency closure, GUID-referrer scan first), genre-neutral vs optional genre packs."
triggers: prefab kit, kit catalog, reuse prefab, reference prefab, import from reference, guid referrer, dead prefab, kit index, bring prefab, bo prefab co san, tai su dung prefab, knife tower style kit
---

# Prefab kit catalog (index)

Opt-in map of the reference kit (read-only catalog of ~250 prefabs plus configs and shaders). It loads nothing by default. Load ONE group skill when the task matches its row; `studio-toolbox-guide` routes task -> skill.

## 1. Groups
| Group | Load | Neutral top items | Optional pack |
|---|---|---|---|
| UI + services | `kit-ui-services` | popup shell + facade, currency bar + spread, quest focus pointer/message/arrow, toast, tabbed shop, revive, settings | IAP card family, daily, rating, jackpot, gacha |
| Characters, skins, AI | `kit-characters-skins-ai` | actor + skin mount, skin asset/unlock/equip, animator guard, bot spawner by tier, trail provider, checkpoint | item/weapon holder, humanoid parkour controller |
| Minigame shells, platforms | `kit-minigame-platforms` | mode registry, mode master + policy, collision dispatch, kill zone, mover/bouncer/conveyor, teleporter | glass bridge, fade-tile arenas, puzzle doors |
| Maps, stages, optimizer | `kit-maps-stages-optimizer` | chunk anatomy, container, hierarchy-order checkpoints, world list asset, per-scene optimizer prefab | tower floors, obby chain, boss set piece, lane stages |
| Assets, configs, shaders | `kit-assets-config-shaders` | config SO + Factory, audio/pool configs, mobile URP tier, TMP outline presets, atlases, localization | triplanar world shader, vertex-colour combiner |

Classification used everywhere: UNIVERSAL (any genre) / OPTIONAL (needs a feature such as shop, IAP, ads) / OPTIONAL GENRE PACK (tower, parkour, typing, paint tycoon) / GAME-SPECIFIC (skip). Genre-neutral first; never import a pack by default.

## 2. How to reuse (in order)
1. Pick the smallest part that does the job; read the group skill and its recipes.
2. GUID-referrer scan BEFORE importing any reference prefab: the reference carries dead prefabs (unused bars, old buttons, duplicate packs, old shooters). Search every `.unity`, `.prefab`, `.asset` for the prefab's GUID (from its `.meta`). Zero referrers = dead: do not import it.
3. Dependency closure (`asset-transfer-closure`): script + `.meta`, nested prefabs, sprites, materials, shader/graph and includes, fonts, audio, config SOs, animator controllers. Keep original GUIDs when intentionally transferring; verify 0 missing references after refresh.
4. Cut genre-bound classes: anything tied to a specific controller, tower, keyboard or mode static is replaced by an interface or event, not copied.
5. Re-author art and strings: product ids, placement ids, message keys, fonts, sprites are per game. Check the installed SketchEngine API before using any named type; never mass-rename namespaces.
6. Wire as prefabs in Edit Mode (`scene-authored-prefabs`), run the gates (`studio-non-negotiables`), keep the provenance line in the plan or commit, not in game code.

## 3. Cross-kit lessons
One Factory facade per feature; events instead of references between tabs and pages; data over prefab variants; prefab YAML field names must equal script fields (a renamed field silently falls back to the script default); decide overlay stacking (tutorial vs banner/native) first; reset static mode flags; baked lists need a re-bake after edits; pre-place and toggle burst FX instead of instantiating.

## Done-check
Group chosen from the table; referrer-scan result recorded; closure verified (0 missing refs, Console clean); neutral vs pack decision written in the plan.

## Pitfalls
Importing a prefab and finding nine hidden dependencies; copying a 1000-line actor instead of its shape; treating the kit as a default instead of opt-in; stale provenance names left in game code.

Related: `reference-index`, `reference-port`, `reference-project-dissection`, `third-party-pack-recon`, `clone-ip-safety`.
