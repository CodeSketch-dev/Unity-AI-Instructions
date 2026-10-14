# Genre reference

Contents: Simulator, Pet/Egg hatching, Steal / carry-and-defend, Tycoon, Treadmill/idle speed, Obby, Tower defense, Fighting/PvP arena, Survival/horror.

## Simulator (collect/sell/upgrade)
- Loop: gather resource (click/swing/walk) -> backpack fills -> sell at hub -> buy tool/backpack/area -> repeat.
- Required: tool with power/speed stats, backpack capacity, sell point, zone gates, rebirth, pets that boost, leaderboard.
- Numbers to study: capacity vs gather rate (a full backpack every 20-40 s early), price steps (x1.5-3 per tier), rebirth multiplier.
- Mobile: auto-gather near nodes, big Sell button when backpack is full.

## Pet / egg hatching
- Loop: earn currency -> buy egg -> hatch (animation) -> pet with rarity -> equip best -> more income -> better eggs.
- Required: egg shop per zone with odds, hatch animation (skippable, auto-hatch), rarity tiers with FX, equip slots, delete/lock, mutations/sizes, pity or luck boosts, index/collection book.
- Numbers: rarity weights (e.g. common 60%, ... legendary 0.1%), income per pet, equip slot growth.
- Mobile: multi-hatch (x3/x10), auto-hatch, skip animation toggle.

## Steal / carry-and-defend (e.g. "steal the X" games)
- Loop: obtain item -> carry to the base (risk while carrying) -> item earns income at base -> upgrade base/cage/defenses -> steal from others.
- Required: carry state (visible, drop/pick-up), safe zone (base) with entry feedback, chasers/bosses that react to carrying, rival players/bots, base slots + upgrade, income tick, rarity-scaled size.
- Numbers: slot count, income per second by rarity, chase speed vs player speed (must be escapable with effort).
- Mobile: one context button that swaps Pick up / Drop; clear carry indicator; haptic when stolen.

## Tycoon
- Loop: stand on pad -> buy a dropper/conveyor/upgrade -> income grows -> unlock next section.
- Required: plot ownership, buy-pad triggers with price, droppers/collectors, unlock chain, save of purchased pads, rebirth.
- Mobile: auto-buy when walking over pads; avoid precise movement.

## Treadmill / idle speed
- Loop: stand/run on treadmill -> speed stat grows -> unlock faster zones/worlds -> bigger treadmills.
- Required: speed stat with big numbers (K/M/B formatting), treadmill tiers with multipliers, leave-treadmill behavior (stat keeps, no snap), zone gates with recommended speed, run animation while on it.
- Numbers formatting: abbreviations (K, M, B, T, Qa, Qi...).

## Obby (obstacle course)
- Loop: reach checkpoints -> stages get harder -> skip stage via ad/purchase.
- Required: checkpoints, kill bricks, moving platforms, timers, stage counter, skip.
- Mobile: forgiving jump/coyote time, camera that doesn't fight the player.

## Tower defense
- Loop: place towers -> waves -> earn -> upgrade -> next map.
- Required: placement grid/paths, enemy waves, tower stats/targeting, speed x2/x3 toggle, loadout, map select.

## Fighting / PvP arena
- Loop: pick weapon -> fight players/bots -> XP/coins -> better weapon.
- Required: hit detection, health/respawn, cooldown abilities, ragdoll/knockback, match flow or open world.
- Mobile: auto-aim assist, big attack button, short TTK tuned for lag.

## Survival / horror
- Loop: gather -> craft -> survive threat -> escape/extract.
- Required: resource nodes, inventory/crafting, threat AI with senses, day/night or timer, extraction.
