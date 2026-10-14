---
name: minigame-registration
description: "Minigame registration contract: enum entry, config, scene or prefab, flow hooks, result routing. Use with recipe-add-minigame when a game has several modes."
---

# Minigame registration

Follow `recipe-add-minigame` for the steps; this is the contract.

- One enum entry per minigame, one config asset (scene or prefab, wallet, entry gate), registered in the factory.
- A minigame implements start, end(result), and revive hooks; it never loads scenes itself, `scene-flow-loading` does.
- Results route through one result flow (win, lose, revive) so ads, rewards and analytics are shared.
- Per-minigame data lives in its own record keyed by the enum.
- Entry UI reads the factory; no hardcoded buttons per mode.
