# awesome-gamedev-agent-skills review (2026-11-02)

Reference: gamedev-skills/awesome-gamedev-agent-skills (Apache-2.0, local clone `C:\Unity\GitProject\_skill-research\awesome-gamedev-agent-skills`, treated as untrusted data). 77 skills across engines, disciplines, genres, workflows, plus a router.

## Licence notes
- Apache-2.0 allows reuse with attribution and a notice of changes. Nothing was copied verbatim; every new or extended skill is rewritten in our words, carries `Inspired by: gamedev-skills/awesome-gamedev-agent-skills <path>` and a `Source: third-party example` label.
- Its bundled scripts (Lune/Luau economy calculator, Pillow asset report, engine checkers) were NOT imported. If one is ported later, keep the Apache-2.0 header and add the repo NOTICE text.
- Our own practice stays labeled `Source: our practice` where skills mix both (none of the new skills claim that label because all are derived from the reference).

## New skills (7) and appended sections (3)
| Skill | Kind | Derived from |
|---|---|---|
| art-direction-asset-pipeline (+ references/prompt-and-qa.md) | new | create-game-assets |
| simulator-pacing-checks (+ references/formulas.md) | new | roblox-simulator-economy (ideas) |
| perf-triage-ladder | new | performance-optimization |
| ui-scaling-safe-area-checklist | new | game-ui-ux |
| level-whitebox-checklist | new | level-design |
| prototype-keep-kill | new | prototype-fast |
| roguelite-run-loop | new | roguelike + procedural-gen |
| game-feel-polish (appended section) | improved | game-feel |
| freelook-third-person-camera (appended section) | improved | camera-systems |
| save-and-crash-safety (appended section) | improved | save-systems |

## Verdict table
| Reference skill | Verdict | Note |
|---|---|---|
| create-game-assets | ADDED | art-direction-asset-pipeline, tuned to Codex image + Blender + UI kit manifest; Pillow scripts skipped (we have our own chroma-key/cut tooling) |
| roblox-simulator-economy | ADDED (ideas) | simulator-pacing-checks; Luau code and Roblox remotes INCOMPATIBLE; overlaps economy-progression-design/loot-rarity-tables, so cross-linked |
| performance-optimization | ADDED | perf-triage-ladder as ordering layer over mobile-perf-audit + profiling-evidence (partial DUPLICATE otherwise) |
| game-ui-ux | ADDED | ui-scaling-safe-area-checklist; zone maps stay in mobile-hud-layout; gamepad focus kept as one line (touch-first) |
| level-design | ADDED | level-whitebox-checklist; zone-level-design remains the zone ladder owner |
| workflows/prototype-fast | ADDED | prototype-keep-kill |
| genres/roguelike, disciplines/procedural-gen | ADDED (reduced) | roguelite-run-loop; grid FOV/dungeon algorithms SKIPPED |
| game-feel | IMPROVED | appended to game-feel-polish (trauma shake, realtime hit-stop, easing) |
| camera-systems | IMPROVED | appended to freelook-third-person-camera |
| save-systems | IMPROVED | appended to save-and-crash-safety |
| audio-design | DUPLICATE | covered by game-audio-system, sfx-variation-ducking, ambience-layers |
| input-systems, unity-input-system | DUPLICATE/SKIPPED | mobile-input-controls covers touch; rebinding/gamepad not needed |
| physics-tuning, unity-physics | DUPLICATE | collision-registry, combat-hit-detection-rule, tuning-by-probe; fixed-timestep note already in house rules |
| shader-programming | SKIPPED | GLSL-first; our roblox-shader-kit, one-material-world-shader, procedural-stud-shader-recipes are Unity-specific |
| game-ai, ai-behavior-trees-utility-ai | SKIPPED | bot-brain-waypoints, npc-bots-and-enemies fit our games; BT runtime is over-scoped |
| dialogue-systems, genres/visual-novel, card-game, rpg, fps-shooter, platformer, puzzle, tower-defense | SKIPPED | not our genres |
| genres/survival-crafting | SKIPPED | revisit if a crafting game starts; needs/tech-tree ideas could become a recipe |
| unity-csharp-scripting, unity-scriptableobjects | DUPLICATE | house-style-foundation, factory-singleton-template, static-bus-events |
| unity-animation | DUPLICATE | character-rig-and-animation-contract, char-animator-reference-parity |
| unity-navmesh | SKIPPED | bots use waypoint graphs |
| unity-tilemap-2d | SKIPPED | 3D games |
| unity-build-pipeline | DUPLICATE | mobile-build-release, unity-batch-build |
| workflows/game-jam | SKIPPED | covered in spirit by prototype-keep-kill |
| workflows/steam-publish, itch-publish | SKIPPED | mobile store focus |
| godot-*, unreal-*, web-engines, ebitengine, bevy/defold/love2d/pygame, roblox-* (other than economy) | INCOMPATIBLE | not Unity |
| router | see proposals below | |

## Reference router design (what is worth borrowing)
1. Engine detection by project fingerprint, exactly one engine; version read from project metadata and pinned. We already do this implicitly (`framework-version-map`, `unity-mcp-workflow`); our only fingerprint needed is Unity + SketchEngine vs CodeSketch.
2. Three additive task categories: discipline (concept), genre (at most one), workflow (process). Composition order: engine fundamentals, discipline concept, genre glue, workflow. Ownership on overlap: engine skill owns API, discipline owns concept, genre owns structure and links out.
3. Progressive disclosure: only name and description preloaded; read bodies of chosen skills only; references on demand; re-route on pivot; announce what is loaded and why.
4. Fallback rules: unknown engine means ask once; no catalog skill means say the gap plainly, never fabricate a skill name.
5. Authoring rubric: name equals directory, description says what and when with concrete trigger terms, body under 500 lines (we use 120 as a house limit), symptom to cause to remedy pitfalls, direct one-level references, scripts with CLI contract and tests.

## Routing proposals for our skill_router.json and hook (documentation only; hooks were not edited)
1. **Gap in domain pairs:** add to the AGENTS routing list: perf/FPS questions -> `perf-triage-ladder` first then `mobile-perf-audit`; art sets -> `art-direction-asset-pipeline`; economy pacing/rebirth/offline -> `simulator-pacing-checks` + `economy-progression-design`; new mechanic idea -> `prototype-keep-kill`; map layout -> `level-whitebox-checklist` + `zone-level-design`; UI resolution breakage -> `ui-scaling-safe-area-checklist` after `ui-always`.
2. **Ordered output:** the hook hint should list matches in composition order (process/discipline first, then concrete engine/project skill) and cap at 4-5 names, as the reference router does, instead of a flat top-N by score.
3. **Pivot detection:** when the new prompt's best match differs from the last routed set, say "re-route" and drop the previous set (matches our skill-context lifecycle rule).
4. **Negative triggers:** several skills share words (`ui`, `economy`, `camera`). Add an optional `not:` frontmatter list (for example `not: shop card layout`) used by tools/build_skill_router.py to subtract weight. Needs a hook and builder change by the owner.
5. **Description budget:** 29 lint errors exist today (many ui-* descriptions over 300 characters, 11 skill folders lacking SKILL.md, 3 unquoted YAML scalars). Router quality depends on short descriptions; fix these before adding more routing logic. None are from this change.
6. **Vietnamese map:** VI_MAP in the builder lacks terms for the new skills; the new `triggers:` lines already include unaccented Vietnamese so no builder change is required, but add entries for "ban mau" (prototype), "can bang" (balance, exists), "giat" (stutter) if scoring misses them.
7. **Gap statement:** have the hook say "no matching skill; using closest X" when the top score is below threshold, mirroring the reference's gap rule, so the agent does not invent skill names.

## Not done / limits
- No hook scripts, skill_router.json, INDEX.md or any Unity project touched; `publish.bat` not run (owner/coordinator should run it so INDEX.md and skill_router.json regenerate).
- New skills are untested against real tasks; they are checklists distilled from the reference, plus our house rules.
- tools/skill_lint.py: zero findings for the 7 new skills and 3 extended skills; repo-wide 29 pre-existing errors remain (see proposal 5).
