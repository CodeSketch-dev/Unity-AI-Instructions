# Company agent skills: Unity mobile game cloning

Project-independent skills for Claude and Codex. Start with `clone-pipeline`; it maps each phase to the skills below and owns the only per-game file, `docs/clone-plan.md` (references, framework, features, fidelity, gates). Skills stay game-independent; names of reference projects live only in that file. Plan and rationale: `../docs/SKILL-SUITE-PLAN.md`.

| Phase | Skill | One line |
|---|---|---|
| Entry | `clone-pipeline` | Which phase, which skills, which gate |
| Entry | `token-efficient-workflow` | Read less, query indexes, batch calls, avoid rework, hand off state |
| Entry | `spec-then-plan` | Clarify -> approaches -> spec -> task plan -> execute (superpowers-grade rigor, no plugin needed) |
| Discover | `gameplay-video-analysis` | Videos/play notes -> flow, UI, numbers, FTUE |
| Discover | `game-clone-recon` | Feature inventory, systems, fidelity labels, staging |
| Discover | `roblox-genre-patterns` | Genre loops and required systems |
| Discover | `reference-index` | One-time index of reference projects; query a feature in one command |
| Discover | `spec-pdf-extract` | PDF/sheet spec -> text + demo images, nothing missed |
| Discover | `clone-ip-safety` | Asset provenance, naming, store-safe |
| Foundation | `unity-project-bootstrap` | Unity 6 mobile setup, URP tiers, platform settings |
| Foundation | `project-context-map` | Compact project map + scan script so agents skip exploration |
| Foundation | `unity-fast-iteration` | Shorter compile/Play loop, asmdefs, batching refreshes |
| Foundation | `debug-cheats-menu` | Dev-only cheat panel template for fast test states |
| Foundation | `unity-code-templates` | Tested number formatter, pool, culler, FPS overlay, press feedback |
| Foundation | `unity-mcp-workflow` | Driving the Editor safely through MCP |
| Foundation | `editor-tool-authoring` | Idempotent, chunked, guarded Editor tools/generators |
| Foundation | `config-driven-feature` | Data -> config -> factory -> events -> wiring |
| Core | `clone-feature-recipes` | Ready checklists for 15 recurring clone features |
| Core | `roblox-character-camera` | Roblox-feel movement and camera, unit conversions |
| Core | `mobile-input-controls` | Joystick, camera drag, multi-touch |
| Core | `zone-level-design` | Zones, scale, readability, perf |
| Core | `npc-bots-and-enemies` | Bots as players, tiers, boss AI |
| Core | `economy-progression-design` | Whole-loop balance, pacing, simulation script |
| Core | `world-batching-culling` | Bake static world/decor, chunk culling, parity checks |
| UI/UX | `mobile-hud-layout` | Zone map: joystick BL, actions BR, settings TL, progress TC, rails |
| UI/UX | `ui-scroll-board` | Scroll lists/boards: inset ScrollRect + rounded Mask, slim scrollbar, spacing, dark preview stage, state plates; `grid_fit.py` |
| UI/UX | `unity-ui` | Canvas/SafeArea/PopupRoot structure and layout validation |
| UI/UX | `ui-style-rules` | Standing visual defaults from past corrections |
| UI/UX | `ui-popup-from-demo` | Popup/HUD from demo images, builder + compare loop |
| UI/UX | `currency-spread-fx` | Rewards fly into HUD currency bars |
| UI/UX | `ui-clone` | UI hub: fidelity process + routing to the UI skills (precedence rules inside) |
| UI/UX | `game-feel-polish` | Juice, FX, haptics, rarity scaling |
| UI/UX | `game-audio-system` | BGM/SFX layer, config, budgets, provenance |
| Port | `reference-port` | Match the reference, compare, adapt not blind-copy |
| Port | `asset-transfer-closure` | Closure resolver script, GUIDs preserved |
| Money | `monetization-integration` | Ads/IAP behind interfaces, compliance |
| Money | `ads-popup-flow` | Ad sheet -> config, scheduler, popups, boosters |
| Money | `unity-iap-port` | Port reference IAP stack, FakeStore verification |
| Quality | `done-means-wired` | Wired + compiled + played before "done" |
| Quality | `unity-qa-playtest` | Test matrix, Editor runs, device checklist |
| Quality | `playmode-script-testing` | Drive Play Mode via MCP scripts + screenshots |
| Quality | `unity-log-triage` | Script that condenses Editor.log/Console to real problems |
| Quality | `unity-debugging` | Root-cause classes and checks |
| Quality | `mobile-perf-audit` | Low-end Android performance audit |
| Ship | `mobile-build-release` | APK/AAB/IPA, signing safety, store checklist |
| Process | `feedback-notes-sync` | Durable feedback log and task queue |
| Process | `multi-agent-coexistence` | Parallel Claude/Codex/Editor protocol + `workspace_guard.py` (snapshot/check/claim) so nobody overwrites newer work |

## Install
Double-click `sync.bat` in the repository root (see `../README.txt`). It copies each folder here to `%USERPROFILE%\.claude\skills\` and `%USERPROFILE%\.codex\skills\`, then start a new session.

## Authoring rules
- One folder per skill, `SKILL.md` with `name` equal to the folder name and a pushy `description` (what + when).
- Body under 500 lines; push detail into `references/`; bundle repeatable code in `scripts/`; templates in `assets/`.
- Explain why, not only what. Stay project-independent; refer to the global house style and the installed framework instead of hardcoding names.
- Never put keys, tokens, keystores or credentials in a skill.
