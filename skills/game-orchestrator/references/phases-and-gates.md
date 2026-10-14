# Phases, gates and budgets (report 21 sec 3.2 and 3.6)

Gate = an artifact plus an automated check. Hours are wall-clock guesses for a 16 h day with 4 file-lane workers and 1 Editor lane; token cap about 8 M including subagents. Recalibrate after the pilot (plan Task 27).

| Ph | Name | Work | Skills (hubs) | Gate (all must pass) | Human | Wall h |
|---|---|---|---|---|---|---|
| 0 | Spec | lint-clean GDD frozen, task graph, short specs for P0 systems, provenance | gdd-intake, spec-then-plan, clone-ip-safety | lint 0 BLOCK; specs exist; graph acyclic; estimate within the day | H1 | 0.75 |
| 1 | Foundation | bootstrap, MCP, URP mobile, folders/asmdefs, framework version map, boot, cheats, project map | unity-project-bootstrap, framework-version-map, boot-sequence-setup | compiles, Console clean, boot scene plays, `PROJECT-MAP.md` | - | 1.25 |
| 2 | Core loop | character, camera, input, zone-1 greybox, checkpoints, pickups, first economy loop | kcc-character-controller, freelook-third-person-camera, platform-kit, zone-level-design | golden path core steps pass in a Play Mode script | H2 | 3.0 |
| 3 | UI | HUD, popups, shop screens from layout contracts, localization, currency fx | ui-builder, ui-pattern-library, ui-validator, ui-visual-qa | validator 0 FAIL, shots at 3 ratios in band, no missing refs | H3 | 3.0 |
| 4 | Content | remaining zones, skins/items/pets from tables, bots, audio, vfx, tutorial | character-skin-system, bots-as-players, game-audio-system | data audit equals GDD tables, all assets resolved, provenance complete | - | 2.5 |
| 5 | Monetization | ads layer (mock), IAP stubs, consent, rewarded flows | monetization-integration, ads-popup-flow | each GDD placement fires with the mock SDK; ad failure never blocks play | - | 1.0 |
| 6 | QA | wiring audit, full golden path, perf, log triage, regression of all earlier gates | qa-fix-retest-loop, mobile-perf-audit, rule-qa-validity | all acceptance criteria green; perf budget on the Mobile tier; Console clean | H4 | 3.0 |
| 7 | Build | Android build, release checklist | mobile-build-release | build succeeds, build gate script passes | H5 | 0.75 |
| - | Slack | reserve | | | | 0.75 |

Per-task limits: 3 attempts then `blocked` plus the simplest fallback; time cap 2x estimate. Phase overrun > 30% triggers the P2 cut. Heavy token cost is Editor/Play loops and screenshots: use cached indexes, project map, short specs, <= 200-word subagent reports, scale-0.4 screenshots (`token-efficient-workflow`).
