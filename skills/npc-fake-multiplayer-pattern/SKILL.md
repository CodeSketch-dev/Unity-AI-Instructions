---
name: npc-fake-multiplayer-pattern
description: "Make a single-player game feel populated: NPC players using the same character stack, names, believable actions, shared-world effects, tuned so the real player is never starved. Use when faking other players."
triggers: npc, fake players, bots, populated world, multiplayer feel, names, vip npc, steal
---

# Fake multiplayer NPCs
- Same character prefab and AI driver as the player; random allowed skins and names; spawn one per frame (`bots-as-players`).
- NPC actions affect the shared world only where the design says so; each owner's rules are data-driven.
- Tune spawn/loot rates so the real player always has something to do.
- Cap count by device tier (`device-tier-policy`, `character-perf-budgets`).
