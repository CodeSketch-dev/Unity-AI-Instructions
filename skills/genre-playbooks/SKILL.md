---
name: genre-playbooks
description: Map a Roblox genre (obby, tower climb, simulator, tycoon, pet collector, steal, escape, racing, mining, arena) to the systems and skills a clone needs. Use at planning when the GDD names a genre.
---

# Genre playbooks

Planning aid, not a design. The GDD is the truth; this lists which systems a clone of the genre usually needs so none is forgotten. Broader catalog: `roblox-genre-patterns`.

| Genre | Systems -> skills |
|---|---|
| Obby / stage runner | `kcc-character-controller`, `platform-kit`, `checkpoint-respawn`, `ladder-climb`, `revive-result-flow`, `intro-camera-flyover` |
| Tower climb | `kcc-character-controller`, `platform-kit`, `checkpoint-respawn`, `freelook-third-person-camera` |
| Simulator / clicker | `economy-loop-archetypes`, `hotbar-inventory`, `recipe-retention-timers` |
| Tycoon | `economy-loop-archetypes`, `recipe-retention-timers`, `zone-level-design`, `recipe-add-pickup`, `npc-bots-and-enemies` |
| Pet / egg collector | `economy-loop-archetypes`, `cosmetic-slot-providers`, `recipe-add-skin-or-item`, `recipe-retention-timers` |
| Steal / base defense | `bot-brain-waypoints`, `simple-boss-patrol-chase`, `teleporter-pad`, `combat-health-status`, `economy-loop-archetypes` |
| Escape / chase | `bot-brain-waypoints`, `simple-boss-patrol-chase`, `checkpoint-respawn`, `nav-traversal-link-tool`, `revive-result-flow` |
| Racing / parkour | `kcc-advanced-movement`, `platform-kit`, `checkpoint-respawn`, `freelook-third-person-camera`, `bots-as-players` |
| Mining / digging | `hotbar-inventory`, `loot-rarity-tables`, `economy-loop-archetypes` (only when evidenced by the GDD) |
| Combat / arena | `combat-hit-detection-rule`, `combat-health-status`, `thrown-bomb-aoe`, `bots-as-players` |

## Always also
Character and camera (`roblox-character-camera`), HUD (`mobile-hud-layout`), shop and currencies when the GDD has them, `tutorial-phase-system`, `settings-pause-offline`, `save-and-crash-safety`, `analytics-events-taxonomy`.

## Proof it plays
A scripted Play Mode run from a clean save reaches the first reference-observed reward and progression interaction at timeScale 1 with a clean Console (`playmode-script-testing`, `rule-qa-validity`). Timing targets come from the GDD or `auto-balance-game`, not this skill.
