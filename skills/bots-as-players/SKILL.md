---
name: bots-as-players
description: "Make bots look and behave like other players in a single-player clone: same character prefab, AI driver, random allowed skins and names, nametags, one-per-frame spawn, fake runner skin swaps. Use when a multiplayer game is cloned offline and the world must feel populated."
---

# Bots as players

Extends `npc-bots-and-enemies` (tiers, population) with the character-side rules from report 19 and `bot-brain-waypoints` (movement brain). Local-only games: bots, fake leaderboards and fake runners substitute for online players (user decision).

- Same `Character` prefab and skeleton as the player; the AI driver writes the same input struct (`kcc-character-controller`).
- Skin: `Factory_Character.GetRandomSkin(type)` from an allowed-types list per mode; avoid duplicates on screen when the pool allows; name from the catalog `bot_names` list (localized defaults, `ui-localization`); optional random aura/trail changed every N revives (`cosmetic-slot-providers`).
- Nametag: one world-space text per visible bot inside a CullingGroup band (~25 m), max 8 visible, text set on change, distinct colour/outline for the local player (`character-emotes-nametags`).
- Spawn: one bot per frame behind a loader task; count = base x device tier scale (`device-tier-policy`); pooled skins keyed by id.
- Fake runners may swap random skins on a configurable cadence observed from the reference; never copy another game's timing.
- Low-end: CullCompletely animators, no real shadows, shared material, ragdoll only for the nearest few (`character-perf-budgets`).
- Rubber band bots by checkpoint distance; bots never write player progress or purchases (`checkpoint-respawn`).
- Fake social: leaderboards seeded from curves, "friends" as named bots (`recipe-fake-leaderboard`).

Verify: 8 bots look distinct, nametags appear only near, frame time holds on the low tier, no per-frame allocation from name/skin lookups.
