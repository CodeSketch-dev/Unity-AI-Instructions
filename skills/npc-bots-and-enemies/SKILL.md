---
name: npc-bots-and-enemies
description: "Bots that act like other players plus enemy/boss AI for single-player clones: shared character systems, tiers, wander/chase, cheap pathing, population. Use when the reference is multiplayer or adding rivals/bosses."
---

# NPC bots and enemies

Single-player clones fake the multiplayer feel with bots. The most maintainable bot is a real player-type character driven by a brain instead of a second code path, so everything the player can do (animations, treadmill, pets, shops, ragdoll) works for bots too.

## Bots as players
1. **Same character, different driver.** Instantiate the player's character type flagged as NPC; replace the input source with a brain that writes into the same input bridge (move vector, jump, action). Reuse stats, animation, ragdoll, nameplates and economy systems.
2. **Goal-driven brain**: a small state machine (idle/wander, go-to-goal, perform, flee, recover). Goals come from the same loop as the player (collect, sell, upgrade, enter zone). Match the reference's bot/other-player behavior first; tune for fun afterwards.
3. **Tiers**: weak/normal/VIP strength, re-rolled periodically so some bots rise to higher zones, run faster or find rarer items; avoid a world of identical weak bots that the player trivially outclasses.
4. **Believable presence**: random names, join/leave over time, varied speeds, occasional mistakes, idle gestures, not all heading to the same target. Cap population by performance (e.g. 6-10 active, others simulated cheaply or hidden).
   - **Skins**: bots randomize their visual skin through the character/skin factory (as the reference projects do), never by reusing the player's equipped skin or data, and never from a serialized skin pool on the bot prefab.
   - **Bot-owned bases** (cages, treadmills) get randomized levels so the world looks populated, obey the same slot caps as the player (upgrade or replace a weaker pet to free a slot), and show their deposited pets and upgrade boards. Standing on another character's treadmill must not train the player.
5. **Fairness**: bots obey the same rules (slots, caps, cooldowns). Do not give them special stealing/griefing powers unless the reference does.
6. **Persistence**: bots' bases/state may be rebuilt each session; keep their data separate from the player's save.

## Enemies and bosses
- **Chase rule** from the reference (e.g. only while the player carries something). Straight-line chase by transform is cheap and often enough; use NavMesh/agents only where the map needs it.
- **Speed**: chaser slightly slower than the player at normal speed so escape is possible with effort; lose-aggro by distance/safe zone.
- **Telegraph attacks** (windup anim, ground marker) for readability on small screens.
- **Scale and look** match the reference per biome; do not apply a global height normalisation that shrinks large bosses.
- **Reactions**: ragdoll/knockback, stun, respawn after a delay; deliver penalties that are fun (drop item, lose time) rather than harsh (lose progress).

## Performance
- Tick brains at 5-10 Hz and stagger by index; steer every frame cheaply.
- Share path/waypoint data; throttle path recomputation by squared-distance threshold; use NonAlloc physics queries with layer masks.
- Disable brains/animators outside view or range; pool bots and effects.

## Verify
Watch 5 minutes of bots from a spectator camera: variety, no stuck loops, no teleport snaps, tiers visible, population stable, no Console errors, frame time acceptable (`mobile-perf-audit`).
