# Recipes

Contents: 1 Interaction reward source, 2 Carry/place flow, 3 Station progression, 4 Zones and gates, 5 Conditional hazard, 6 Commerce, 7 Upgrade surfaces, 8 Prestige, 9 Timed rewards, 10 Collection, 11 Optional automation, 12 Bots, 13 Cosmetics, 14 Optional ad rewards, 15 Offline accrual.

Each recipe: **Behavior / Data / Config / Events / UI / Edge cases / Perf / Verify**. Recipes define structure and invariants, never prices, boosts, cooldowns, income, HP, or other balance constants. If a reference value is not evidenced, use a tunable placeholder and let the balance pass generate it.

## 1 Interaction reward source
- **Behavior**: a GDD-defined world source receives its configured interaction and emits the configured reward/state transition.
- **Data/Config**: source identity, ownership, interaction cadence, reward table and respawn policy are authored data.
- **Events/UI**: use feature-owned state/reward events and only GDD-specified feedback.
- **Edge cases/Verify**: concurrent actors, interruption, despawn/respawn, save/load and reward-once behavior.

## 2 Carry and owned-slot flow
- **Behavior**: acquire, carry, place, release, or transfer the GDD-defined entity only through its documented interaction states.
- **Data/Config**: instance identity, slot capacity, placement rules and optional production rules are authored data.
- **Events/UI**: feature-owned transition events and only the required interaction feedback.
- **Edge cases/Verify**: capacity, interruption, transfer, disconnect/pause, save/load and bot ownership rules.

## 3 Station-based progression
- **Behavior**: entering a configured station starts the GDD-defined action; exiting stops it without duplicating gains or invalidating current state.
- **Data**: the GDD-selected stat and station state. **Config**: tiers, effect, cadence, unlock channels, and display format are tunable fields populated only from evidence or the balance pass.
- **Events/UI**: use feature-owned state-change events and only the feedback the GDD specifies.
- **Edge cases**: ownership, overlapping stations, an upgrade during use, and the applicable bot policy.
- **Verify**: configured progression, exit behavior, ownership rules, and persistence where selected.

## 4 Zones, gates, banners
- **Behavior**: world split into zones with a gate stat (speed); entering shows a banner (zone name + recommended value) that slides in and fades; fog/skybox per zone.
- **Data**: highest zone reached. **Config**: zone list (name, gate, recommendation, theme and GDD-defined content references).
- **Events**: `ZoneEntered`. **UI**: banner; region label at top (shrinks after intro).
- **Edge cases**: rapid back-and-forth at a border (hysteresis); teleport; recommended speed includes a safety margin over chaser speed.
- **Perf**: per-zone far-clip and decor culling (`world-batching-culling`).
- **Verify**: monotonic gates (audit), banner plays once per entry.

## 5 Boss chase and safe zone
- **Behavior**: a configured hazard activates only under the GDD-defined condition; a configured safe rule ends it and the configured catch outcome resolves it.
- **Data**: none persistent. **Config**: chase speed per boss, aggro range, recovery time.
- **Events**: `BossChaseStarted/Ended`, `PlayerCaught`. **UI**: warning indicator (reference asset), chase SFX loop.
- **Edge cases**: condition removal, safe-zone boundary flicker, navigation obstruction, and fairness at GDD-defined tuning.
- **Verify**: carry -> boss reacts -> reach safe zone -> chase ends; no boss when not carrying.

## 6 Shops (tools, trails, skins)
- **Behavior**: world stall or popup; items with price, owned/equipped state; purchase deducts currency, equips.
- **Data**: owned set, equipped id. **Config**: item list (price, rarity, prefab/icon).
- **Events**: `ItemBought`, `ItemEquipped`. **UI**: popup via the project popup manager; stalls placed beside the path, never narrowing it.
- **Edge cases**: insufficient funds (no success sound), already owned, equip while carrying, IAP-gated items. A skin shop must change the real character (look at the world, not only the data), cover multi-part skins (outfit + face + hair + hat on the same skeleton), and be checked under the game's own lighting (materials tuned for another sun look dull).
- **UI**: list + preview layout per `ui-scroll-board`; sell only through the channels the game really has (reward ad, IAP, currency); drop states for systems that do not exist (no daily -> no daily plate).
- **Verify**: buy -> persists after restart; failed purchase has no side effects.

## 7 Upgrade surfaces
- **Behavior**: a GDD-specified world or UI surface presents level, cost and effect; its interaction and visual states are evidence-driven.
- **Data**: feature levels. **Config**: level/effect tables with generated or observed values; the recipe does not prescribe prices.
- **UI**: real tap collider, range-based fade that also disables raycasts, press-scale feedback, tappable from reference distance.
- **Edge cases**: max level state; applicable bot presentation; configured reward-channel state.
- **Verify**: tap from far/near, unaffordable, max level.

## 8 Rebirth / prestige
- **Behavior**: reset progress for a permanent multiplier; confirmation popup showing what resets/keeps; first available at the tuned time.
- **Data**: rebirth count, multiplier. **Config**: requirement curve, multiplier curve, keep-list.
- **Edge cases**: interrupted reset; ads/IAP entitlements preserved.
- **Verify**: audit that the first rebirth lands in the target window.

## 9 Daily reward and streak
- **Behavior**: 7-day (or similar) calendar, claim once per day, streak resets after a miss, optional ad to double.
- **Data**: last claim time, streak. **Config**: reward table.
- **Edge cases**: device clock changes (use a tolerance and, if possible, server time); timezone; claim twice; app resumed across midnight.
- **UI**: top rail button with a badge when claimable.

## 10 Collection index
- **Behavior**: grid of all species by biome with discovered/undiscovered state, progress bars (collected, rewards), claimable milestones.
- **UI**: compact popup, 5-column grid, biome column with sliced ribbons, detail column; port from the reference 1:1 (`reference-port`).
- **Edge cases**: new species discovered while the popup is open; mutations/sizes.

## 11 Optional automation
- **Behavior**: each GDD-authorized automation has explicit eligibility, target, cancellation, persistence and UI rules.
- **Edge cases**: target loss, mutually exclusive states, and forbidden transactions.

## 12 Bots as players
See `npc-bots-and-enemies`: real characters with a brain, strength tiers, same caps and systems, random skins from the factory, populated bases.

## 13 Trails and cosmetics
- **Behavior**: equippable trail VFX tied to rarity (rarer = prettier, rainbow must not look black); shown on player and bots.
- **Data**: owned/equipped trail. **Config**: trail prefab + icon per rarity (mapping file, idempotent import `asset-transfer-closure`).
- **Perf**: pooled trail renderers, capped particle counts.

## 14 Rewarded-ad boosts
- **Behavior**: optional temporary acceleration, free action, or revive when observed; never forced.
- **Architecture**: `monetization-integration` (interfaces + Editor mock); reward exactly once; works offline-safe (button hides when no ad ready).
- **Verify**: success/failure/cancel paths in the mock; boost timer persists.

## 15 Offline earnings
- **Behavior**: on return, grant income for min(time away, cap) at a reduced rate with a collect popup (optional ad to double).
- **Edge cases**: clock tampering, very long absences, first launch (no previous timestamp).
- **Verify**: simulate by editing the saved timestamp (cheat menu).
