---
name: clone-pipeline
description: "Entry point for cloning a Roblox-style game to Unity mobile: maps phase -> skills -> gates, and holds the per-game docs/clone-plan.md. Use at project start, \"what's next\", or when unsure which skill applies."
---

# Clone pipeline

Cloning succeeds when each phase ends with something a human can play and a short written artifact. This skill tells you which phase you are in and which skills to load. Skills are listed by name; load them when entering the phase.

## Find the phase
Read `docs/clone-plan.md` and `docs/feedback-notes.md` if present. No plan yet -> phase 0: copy `assets/clone-plan.template.md` to `docs/clone-plan.md` (it holds the game's references, framework, features, fidelity and gates; **this file is the only per-game config, the skills stay generic**). Otherwise continue at the first unfinished gate.

| Phase | Goal | Load these skills | Gate artifact |
|---|---|---|---|
| 0 Discover | Know the game from evidence | `gameplay-video-analysis`, `spec-pdf-extract` (if a PDF/sheet spec), `game-clone-recon`, `roblox-genre-patterns`, `reference-index`, `clone-ip-safety` | `docs/gameplay-analysis.md`, `docs/clone-plan.md`, `docs/asset-provenance.md` |
| 1 Foundation | Project ready for fast iteration | `unity-project-bootstrap`, `project-context-map`, `unity-mcp-workflow`, `unity-fast-iteration`, `editor-tool-authoring`, `debug-cheats-menu`, `config-driven-feature`, `unity-code-templates` | compiles, MCP connected, mobile URP set |
| 2 Core loop | Vertical slice playable | `roblox-character-camera`, `mobile-input-controls`, `clone-feature-recipes`, `zone-level-design`, `world-batching-culling`, `economy-progression-design`, `npc-bots-and-enemies` | 3-minute loop playable on device |
| 3 UI/UX | HUD parity and feel | `ui-pattern-library` (standard screens), `ui-clone` (hub: routes to `mobile-hud-layout`, `unity-ui`, `ui-style-rules`, `ui-popup-from-demo`, `ui-scroll-board`), `currency-spread-fx`, `game-feel-polish`, `game-audio-system` | screenshots match at 3 aspect ratios |
| 4 Port | Bring over reference content | `reference-port`, `asset-transfer-closure` | no missing references |
| 5 Monetize | Hooks and consent | `monetization-integration`, `ads-popup-flow`, `unity-iap-port` | mocked ads/IAP flows |
| 6 Quality | Prove it works | `done-means-wired`, `unity-qa-playtest`, `playmode-script-testing`, `unity-debugging`, `unity-log-triage`, `mobile-perf-audit` | test matrix + perf numbers |
| 7 Ship | Release candidate | `mobile-build-release` | signed build, store checklist |

Always on: `token-efficient-workflow` (read less, query indexes, batch), `spec-then-plan` (plan every non-trivial task before building it), `feedback-notes-sync`, `multi-agent-coexistence`.

## Working agreements
- **Vertical slice first.** Greybox the whole loop before polishing any one system; polish before breadth only where the user asks.
- **One task, one reference.** Every task names its evidence (video timestamp, screenshot, reference path). No evidence -> ask the human to supply a screenshot or timestamp instead of guessing.
- **Fidelity labels** (`exact`, `faithful`, `free`) from `game-clone-recon` decide how strict comparison is.
- **Plan before building.** Anything bigger than a small edit goes through `spec-then-plan`: spec, task plan with verification, then execute task by task.
- **Finish before starting.** Complete wiring and verification of the current task before the next; queue new requests.
- **Human checkpoints.** After gates G2, G3 and G6, stop and ask the human to play the build and react; their reactions are the most valuable input in the whole process.
- **Report honestly**: verified vs assumed, and what remains.

## When the human says...
- "It looks different" -> `reference-port` + `ui-clone`.
- "Ads / IAP / popups from a sheet" -> `spec-pdf-extract`, then `ads-popup-flow` / `unity-iap-port`.
- "Can't click / not showing / nothing happens" -> `done-means-wired`, then `unity-debugging`.
- "Too grindy / too easy / boring" -> `economy-progression-design`, `game-feel-polish`.
- "Laggy / hot phone" -> `mobile-perf-audit`.
- "Ready for the store?" -> `clone-ip-safety`, `monetization-integration`, `mobile-build-release`.
