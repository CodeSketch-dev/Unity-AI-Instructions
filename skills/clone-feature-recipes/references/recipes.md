# Recipes

Contents: 1 Egg break and hatch, 2 Pet carry and base income, 3 Treadmill and speed, 4 Zones, gates, banners, 5 Boss chase and safe zone, 6 Shops, 7 Upgrade boards, 8 Rebirth, 9 Daily reward and streak, 10 Collection index, 11 Auto buttons, 12 Bots as players, 13 Trails and cosmetics, 14 Rewarded-ad boosts, 15 Offline earnings.

Each recipe: **Behavior / Data / Config / Events / UI / Edge cases / Perf / Verify**.

## 1 Egg break and hatch
- **Behavior**: eggs spawn in zone slots with HP by biome/rarity/luck; the tool hits at a cadence (cooldown measured from the real animation clip); on break, FX + a pet appears (or hatch animation for shop eggs).
- **Data**: pickaxe/tool level, eggs broken counter, owned/discovered pets. **Config**: egg tiers (HP, rarity weights, luck), tool table (damage, price, cadence) in a registry; spawn slots per zone.
- **Events**: `EggHit`, `EggBroken(egg, owner)`, `PetObtained`. **UI**: egg label (name, rarity, HP bar `cur/max`), hit feedback, rarity-colored reveal.
- **Edge cases**: two players/bots hitting one egg; breaking while carrying; egg despawn; luck display counts up during reveal; no eggs left in zone (respawn timer).
- **Perf**: pool eggs and FX; world labels via one batched text system; hit cooldown gates SFX.
- **Verify**: break -> pet appears at the same frame count at 1x; fresh save works; HP/time table within the balance audit (`economy-progression-design`).

## 2 Pet carry and base income
- **Behavior**: pick up a pet (contextual button), carry it (arms up, speed rules from reference), place it in a base slot; each pet earns $/s while placed; carry timer pauses.
- **Data**: pet instances (id, rarity, size/mutation, level), base slots and level. **Config**: pet species (income, size curve), slot count and multiplier per base level.
- **Events**: `PetPickedUp`, `PetDropped`, `PetPlaced`, `IncomeTick`. **UI**: single Interact button (Pick up/Drop swap), carry info card above the hotbar, base pet labels ($/s, rarity, name).
- **Edge cases**: full base keeps pet in hand; bots' bases obey the same cap; drop while chased; disconnect/app pause with pet in hand; first-time FX only.
- **Perf**: income ticks batched in one manager; pets in base are pooled meshes, labels throttled.
- **Verify**: pick up -> place -> income credited to wallet; slot cap enforced; save/load keeps placed pets.

## 3 Treadmill and speed
- **Behavior**: standing on a treadmill trains Speed over time (auto, no run button); leaving stops gain without snapping; run animation plays while on it; floating "+speed" popups on each tick.
- **Data**: speed stat, treadmill level. **Config**: treadmill tiers (multiplier, price), tick interval, big-number formatting.
- **Events**: `SpeedChanged`, `TreadmillEntered/Exited`. **UI**: speed bar, upgrade board, popup text.
- **Edge cases**: other characters' treadmills never train the player; treadmill footprint must not block the base door; tier upgrade while standing on it.
- **Verify**: speed increases at the configured rate; leaving keeps value; bots use it too.

## 4 Zones, gates, banners
- **Behavior**: world split into zones with a gate stat (speed); entering shows a banner (zone name + recommended value) that slides in and fades; fog/skybox per zone.
- **Data**: highest zone reached. **Config**: zone list (name, gate, recommended, theme, egg table, boss).
- **Events**: `ZoneEntered`. **UI**: banner; region label at top (shrinks after intro).
- **Edge cases**: rapid back-and-forth at a border (hysteresis); teleport; recommended speed includes a safety margin over chaser speed.
- **Perf**: per-zone far-clip and decor culling (`world-batching-culling`).
- **Verify**: monotonic gates (audit), banner plays once per entry.

## 5 Boss chase and safe zone
- **Behavior**: bosses chase only under the reference's condition (e.g. while carrying a pet); straight-line chase by transform; safe zone (home) stops them with entry FX once; catching drops the pet/ragdolls.
- **Data**: none persistent. **Config**: chase speed per boss, aggro range, recovery time.
- **Events**: `BossChaseStarted/Ended`, `PlayerCaught`. **UI**: warning indicator (reference asset), chase SFX loop.
- **Edge cases**: dropping the pet ends the chase; safe-zone boundary flicker; boss stuck behind walls; chase speed vs player speed escapable with effort.
- **Verify**: carry -> boss reacts -> reach safe zone -> chase ends; no boss when not carrying.

## 6 Shops (tools, trails, skins)
- **Behavior**: world stall or popup; items with price, owned/equipped state; purchase deducts currency, equips.
- **Data**: owned set, equipped id. **Config**: item list (price, rarity, prefab/icon).
- **Events**: `ItemBought`, `ItemEquipped`. **UI**: popup via the project popup manager; stalls placed beside the path, never narrowing it.
- **Edge cases**: insufficient funds (no success sound), already owned, equip while carrying, IAP-gated items. A skin shop must change the real character (look at the world, not only the data), cover multi-part skins (outfit + face + hair + hat on the same skeleton), and be checked under the game's own lighting (materials tuned for another sun look dull).
- **UI**: list + preview layout per `ui-scroll-board`; sell only through the channels the game really has (reward ad, IAP, currency); drop states for systems that do not exist (no daily -> no daily plate).
- **Verify**: buy -> persists after restart; failed purchase has no side effects.

## 7 Upgrade boards (cage, treadmill, tool)
- **Behavior**: world board at the base edge showing level, price, benefit; tap to upgrade; price turns red when unaffordable; fixed (not billboarded).
- **Data**: levels. **Config**: price and effect tables.
- **UI**: real tap collider, range-based fade that also disables raycasts, press-scale feedback, tappable from reference distance.
- **Edge cases**: max level state; other cages (bots) show boards too; ad-reward button wired.
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

## 11 Auto buttons
- **Behavior**: Auto-Hit works only near eggs; Auto-Collect picks up nearby drops; toggle state persists in session; sits centered above the hotbar, small.
- **Edge cases**: ending automatically when target is gone or when carrying; never auto-buy.

## 12 Bots as players
See `npc-bots-and-enemies`: real characters with a brain, strength tiers, same caps and systems, random skins from the factory, populated bases.

## 13 Trails and cosmetics
- **Behavior**: equippable trail VFX tied to rarity (rarer = prettier, rainbow must not look black); shown on player and bots.
- **Data**: owned/equipped trail. **Config**: trail prefab + icon per rarity (mapping file, idempotent import `asset-transfer-closure`).
- **Perf**: pooled trail renderers, capped particle counts.

## 14 Rewarded-ad boosts
- **Behavior**: optional "x2 income for N minutes", "free hatch", revive; never forced.
- **Architecture**: `monetization-integration` (interfaces + Editor mock); reward exactly once; works offline-safe (button hides when no ad ready).
- **Verify**: success/failure/cancel paths in the mock; boost timer persists.

## 15 Offline earnings
- **Behavior**: on return, grant income for min(time away, cap) at a reduced rate with a collect popup (optional ad to double).
- **Edge cases**: clock tampering, very long absences, first launch (no previous timestamp).
- **Verify**: simulate by editing the saved timestamp (cheat menu).
