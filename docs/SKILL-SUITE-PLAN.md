# Skill suite plan: cloning Roblox-style games to Unity mobile (Android/iOS)

## Context
The company builds Unity mobile games (Android + iOS), mostly clones of Roblox games. The human plays the reference game and watches YouTube gameplay to learn the main flow, then "vibe codes" it with AI agents (Claude, Codex) through Unity MCP. The suite must make that loop fast, repeatable and safe, independent of any single project.

## Pain points observed in real sessions (from the first project run with this workflow)
| Pain point | Root cause | Answered by |
|---|---|---|
| "Looks different from the reference" repeated many times | Work started from memory, no side-by-side comparison, offsets copied blindly | `reference-port`, `ui-clone`, `gameplay-video-analysis` |
| Missing material/texture/prefab after transfer | Only the prefab was copied | `asset-transfer-closure` |
| "Can't click / not showing" after delivery | Scripts written, wiring skipped (collider, prefab override, config asset) | `done-means-wired`, `unity-qa-playtest` |
| UI overlap, wrong anchors, broken 9-slice, mirrored text | No layout rules for mobile HUD | `mobile-hud-layout`, `ui-clone` |
| Lost decisions after context compaction | No durable memory of feedback | `feedback-notes-sync` |
| Two agents overwriting each other (one edits from a stale copy and loses the other's change) | Memory of the file treated as truth; Editor holding old scenes | `multi-agent-coexistence` protocol + `workspace_guard.py`, rule in `AGENTS.md` |
| Economy feels flat or grindy | Numbers invented ad hoc | `economy-progression-design`, `roblox-genre-patterns` |
| Lag on low-end Android | Unmeasured hot paths | `mobile-perf-audit` |
| Game feels dead | No juice pass | `game-feel-polish` |
| Legal exposure from ripped assets/names | No provenance tracking | `clone-ip-safety` |
| Unity hung (~31 GB RAM), unsaved scene lost, duplicated objects from MCP retries | Unguarded, non-idempotent generator scripts | `editor-tool-authoring`, `unity-mcp-workflow` |
| Map with 3767 renderers / 149 materials | Per-object materials, no baking | `world-batching-culling` |
| Price curve that would take ~165 years | Tables tuned in isolation | `economy-progression-design` (whole-loop balance) |
| QA route found 0 pets at timeScale 60 | Game-second timers shrink in real time; polluted save | `unity-qa-playtest` |
| Re-work after jumping into code | No written spec/plan | `spec-then-plan` |
| No sound / unwired audio | No audio layer plan | `game-audio-system` |

## Pipeline (phases and gates)
```
0 Discover  -> gameplay-video-analysis, game-clone-recon, roblox-genre-patterns, clone-ip-safety
1 Foundation-> unity-project-bootstrap, unity-mcp-workflow, config-driven-feature
2 Core loop -> roblox-character-camera, mobile-input-controls, zone-level-design, npc-bots-and-enemies, economy-progression-design
3 UI/UX     -> mobile-hud-layout, ui-clone, game-feel-polish
4 Port      -> reference-port, asset-transfer-closure
5 Monetize  -> monetization-integration
6 Quality   -> done-means-wired, unity-qa-playtest, unity-debugging, mobile-perf-audit
7 Ship      -> mobile-build-release
Always on   -> feedback-notes-sync, multi-agent-coexistence
Entry point -> clone-pipeline (maps the phase to the skills and gates)
```
Gates (each ends with a human-playable build and a short written artifact in `docs/`):
- G0 Discovery: `docs/gameplay-analysis.md`, `docs/clone-plan.md`, `docs/asset-provenance.md` started.
- G1 Foundation: project compiles, mobile URP profile, MCP connected, folder/asmdef layout done.
- G2 Vertical slice: core loop playable on device for 3 minutes (move, collect, earn, upgrade).
- G3 UI parity: HUD matches reference screenshots at 3 aspect ratios.
- G4 Content breadth: zones, items, bosses/bots, shops.
- G5 Monetization hooks mocked in editor, consent flow decided.
- G6 QA: test matrix passed, perf budget met on a low-end device.
- G7 Release candidate: signed build, store checklist.

## Skill catalogue (49 skills)
Each skill: one `SKILL.md` (pushy description, why-driven steps, under 500 lines), optional `references/`, `assets/`, `scripts/`.

Discover: `clone-pipeline`, `gameplay-video-analysis`, `game-clone-recon`, `roblox-genre-patterns`, `reference-index`, `clone-ip-safety`
Foundation: `unity-project-bootstrap`, `project-context-map`, `unity-mcp-workflow`, `unity-fast-iteration`, `editor-tool-authoring`, `debug-cheats-menu`, `config-driven-feature`, `unity-code-templates`
Core: `clone-feature-recipes`, `roblox-character-camera`, `mobile-input-controls`, `zone-level-design`, `world-batching-culling`, `npc-bots-and-enemies`, `economy-progression-design`
UI/UX: `mobile-hud-layout`, `ui-scroll-board`, `ui-clone`, `game-feel-polish`, `game-audio-system`
Port: `reference-port`, `asset-transfer-closure`
Money: `monetization-integration`
Quality: `done-means-wired`, `unity-qa-playtest`, `unity-debugging`, `unity-log-triage`, `mobile-perf-audit`
Ship: `mobile-build-release`
Added later: `ui-pattern-library`, `spec-pdf-extract`, `ads-popup-flow`, `unity-iap-port`, `currency-spread-fx`, `ui-popup-from-demo`, `ui-style-rules`, `unity-ui`, `playmode-script-testing`
Process: `token-efficient-workflow`, `spec-then-plan`, `feedback-notes-sync`, `multi-agent-coexistence`

## Framework model (game-independent)
- Skills = generic engine. `clone-pipeline` = orchestrator. `docs/clone-plan.md` (template in `clone-pipeline/assets`) = the only per-game config: references table (name, path, index, source-of), framework, features with fidelity, gates.
- Reference projects are data, never hardcoded in skills; recipe skills (`currency-spread-fx`, `unity-iap-port`, `ads-popup-flow`) resolve real class names via `reference-index` first.
- Precedence: reference/spec > user's latest message > team defaults (`ui-style-rules`, `mobile-hud-layout`).
- Token budget: descriptions kept to ~1-2 lines (about 3k tokens for the whole catalogue); detail loads on demand from `references/`.
- UI is a hub (`ui-clone`) routing to single-concern skills; one source of truth per rule.

## Design principles
1. Evidence before code: every task cites a reference (video timestamp, screenshot, file path).
2. Fidelity labels (exact / faithful / free) decide how strictly to match.
3. Done = wired + compiled + played, with honest reporting of what was not verified.
4. Project-independent: skills inspect the actual framework, never assume package names; house style comes from the global AGENTS.md.
5. Mobile low-end is the default target.
6. Skills explain *why*, so agents can generalize instead of following brittle rules.

## Rollout
1. Install by double-clicking `sync.bat` (copies `AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, and `skills/` to `~/.claude/skills` and `~/.codex/skills`; pulls first when the repo is clean).
2. Pilot on the next clone; collect misses in `docs/feedback-notes.md` of that project.
3. Monthly: fold recurring misses back into the relevant skill; run trigger-description evals with `skill-creator` on the most-used skills.
4. Ownership: one maintainer per phase; changes by PR to this repo.

## Not covered yet (candidates)
Localization, analytics/event taxonomy, backend/leaderboards/cloud save, multiplayer/netcode, trading systems, accessibility. Add when a project needs them.

## Evidence base
The suite was derived from the first project run with this workflow (`thunder-break-egg`): its `docs/feedback-notes.md` (user corrections and rejected results), `docs/superpowers/{specs,plans}` (the planning format that worked), `docs/balance/` (economy audits), and the editor tools it needed (bake/installer/import scripts). Every rule in a skill that says "learned"/"past projects" comes from there. Refresh the skills from each new project's feedback notes after its gates (rollout step 3).

## Verification of the suite
- Structure: every skill folder has `SKILL.md` with `name` = folder name and a `description` (checked by script).
- Tools: `asset-transfer-closure/scripts/resolve_closure.py` was run against a real reference project (read-only) in dry-run and apply modes into a throwaway target; GUIDs and `.meta` were preserved and a second run reported every member as present. `economy-progression-design/scripts/simulate_economy.py` ran and printed the pacing table. `sync.bat` (the single installer; `sync.ps1` was removed) was tested in a throwaway home folder: fresh install, backup of an existing file, idempotent rerun, partial skill update, pull of a new remote commit on a clean repo.
- Not yet verified: trigger quality of each description (needs the skill-creator description evals), and a full pilot on a new clone.

## Efficiency layer (tokens and speed)
Added after the first pilot of the suite. Goal: the agent spends tokens on building, not on re-learning.
| Waste | Skill | Mechanism |
|---|---|---|
| Re-exploring the project every session | `project-context-map` | 100-150 line map + `unity_project_scan.py` draft |
| Blind grep in 2-3k-script reference projects | `reference-index` | one-time JSON index; `query`/`show` in ~0.1 s |
| Reading huge scenes/prefabs/logs | `token-efficient-workflow`, `unity-log-triage` | summarize with tools; filtered output; delegate wide searches |
| Compile/Play waiting | `unity-fast-iteration` | asmdefs, batched refresh, Enter Play Mode options with static reset |
| Grinding to reach a test state | `debug-cheats-menu` | dev-only cheat panel, scenario recipes |
| Redesigning common features | `clone-feature-recipes` | 15 recipes with data/config/UI/edge-case checklists |
| Rewriting helpers | `unity-code-templates` | tested number formatter and small Unity utilities |
Reference indexes for the three team references were built once into a shared folder (outside any project) and should be rebuilt when a reference changes.

Verified: scan script on three real reference projects (1.9k-3.6k scripts, 2.4k-3.2k prefabs, ~1 minute each; query ~0.1 s); log script on a synthetic log and a real Editor.log (12.5k lines -> 0-2 rows); `NumberFormatter` compiled and checked with 27 cases (found and fixed a floating-point bug). Not verified: Unity compilation of the other templates, and the real token/time savings (needs a measured pilot).
