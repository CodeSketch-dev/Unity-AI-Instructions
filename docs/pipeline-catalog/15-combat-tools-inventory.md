# 15 - Combat, tools, inventory (reverse-engineering + design)

Scope: Roblox-style tools/weapons, melee/ranged/thrown, pickaxe/dig/bomb, upgrades, hotbar/inventory, equipment, item data model, rarity, loot, projectiles, game feel, enemy/boss, status effects. Then a data-driven ToolSystem + CombatSystem + Inventory skeleton.
Read-only. Nothing compiled or run in Unity (no MCP session). Tags: **[V]** read in cited file/asset, **[I]** inferred.
Short paths: **KT** = `knife-tower/knife-tower-troll-unity/Assets/_Game` (CodeSketch v1), **TBE** = `thunder-break-egg/break-and-steal-unity/Assets/_Game` (SketchEngine v2, vibe-coded), **CT** = `climb-and-jump-tower/climb-tower-unity/Assets` (legacy CFramework + Digger plugin), **ME** = `monkey-escape/monkey-escape-unity/Assets/_Game`. `S/` = `Scripts/`.
problox, ride-a-pet, steal-an-egg: filename grep for weapon/combat/damage/health/attack/tool/pickaxe/hotbar/projectile/bomb found nothing usable (only problox keyboard tooling) [V grep]. Not deep-read.

---------------------------------------------------------------------------
## 1. Headline findings

1. **No project has a generic HP/damage model for characters.** KT characters have no HP: a hit = ragdoll knockback (`Character.OnHit` -> `MarkRagdoll(2.5 s)`), a one-shot weapon or burn = `Kill()`, a shield absorbs one hit [V `KT S/Logic/Character/Character_Attack.cs` OnHit, `Character.cs` L318-360, L529-545, `Game/GameStatic.cs` RagdollDuration 2.5]. Numeric HP exists only on **eggs** (TBE, double HP) and the **boss event** (percent) [V]. A new combat system must introduce HP; there is no reference implementation for player HP, so numbers for it are [I].
2. **"Tool" = data asset + held visual + one swing pipeline.** KT `Item_Asset` (SO) holds `[SerializeReference] Item_Info` (polymorphic, subclasses `Item_Info_Weapon/Cape/CoilSpring/SpeedBoost`); TBE `Pickaxe_Asset` is a flat SO with 15 tiers; CT `PickaxeConfig`/`BombConfig` are flat SOs with 37 / 9 tiers [V].
3. **Hit detection is always cheap and non-physical for melee**: NonAlloc overlap or a cached target list + squared range + cone dot, applied on an animation impact time, never a per-frame weapon collider [V KT/TBE]. Projectiles use a real collider (KT `OnCollisionEnter` + `OptScriptLookup.TryFindFirst`) [V].
4. **Impact is scheduled at a normalized point of the swing clip** (TBE `Factory_SAB.DigImpactNormalized` 0.88; KT fixed 0.25 s hit delay after a 0.1 s fx delay) [V].
5. **Upgrade curves are formula/table driven and snapped to "nice" numbers** (TBE `EggBalanceFormula`, x4 power per tier, `RoundNice`) [V].
6. **Gaps (no evidence found):** hit-stop (only `Time.timeScale` pause/resume in `GameStatic.cs`), crit system in KT/TBE (CT has a critical damage-text sprite only), per-kill currency in KT, nametag code (KT `Character_UI` read only for effect icon fields), knockback numbers for KT besides ragdoll force. Say so; do not invent.
7. **Anti-patterns to avoid when cloning:** per-weapon `switch (Item_Type)` for throw logic (`Character_Attack_Throw.cs`), `new HashSet/List` every 0.15 s in `Character_EventTick`, `try{}catch{}` around event subscribe, `gameObject.Create()` (Instantiate) for the banana throw instead of the pool, `Data_Game.InfinityHit` hard-coding cooldown 0.6 inside attack code [V all in KT].

---------------------------------------------------------------------------
## 2. Tools and weapons (equip, hold, swing, cooldown)

### 2.1 KT weapon pipeline [V unless noted]
| Stage | Where | Behaviour / number |
|---|---|---|
| Equip request | `Item_Asset.Equip()` -> `StaticBus<Event_Item_Equipped>` | `Data_Item.Equipped` (battle) vs `EquippedBuff` (support, session-only: cleared in `Data_Item.Init`) |
| Per-character equip | `Character_Item.StaticBus_ItemEquipped` -> `Equip(Item_Info)` | `Release()` old (undo `MoveSpeedMultiplier`, coil `JumpVerticalMultiplier`), skin `DoEquipItem`, `Boost()` new, anim speed source, `EventEquipped` |
| Held visual | `Item_Activator` (on skin): `_items[]` -> `Dictionary<Item_Type, Item>`, `_handR` | child items are pre-baked and toggled active, not instantiated |
| Attack entry | `Character_Attack.Attack()` -> `IsAttackAllowed()` -> `TaskAttack()` (UniTask) | gates: global `Item_Static.IsItemAvailable`, `_isReady` (cooldown), equipped `IsAttackable`, `Character.IsReadyForAttack()` |
| Target gather | `Character.OtherDetector` snapshot array (no physics) else `Physics.OverlapSphereNonAlloc(pos, AtkRange, buf32, LayerAttackable)` | buffer 32, `_verticalTolerance` 2 m (non-player), planar square test then front-dot |
| Range | `AtkRange = Range x skinScale x rangeMult x (Player: PlayerAttackRangeExtra, AI: AIAttackRangeMultiplier)` | `Range` from weapon info |
| Cone | half angle 90 deg (dot >= cos90 = 0, so full front half-plane); player adds `PlayerAttackAngleExtra` clamped 0..180 | |
| Timing | fx at t=0, `PlayFxUsed` at +0.1 s, hit applied after `defaultHitDelay` 0.25 s (fly-carpet 0.1 s) | `AttackDuration` 0.25 s also move-lock time when `IsMoveLockedWhenAttacking` |
| Cooldown | `TaskCooldown` -> `_isReady=true` after `Cooldown`; player HUD `GUI.Cooldown(t)` fills `_imgAttackCooldown` | cheat `InfinityHit` forces 0.6 s |
| Hit | `OnHit(target)`: immune if `IsTinyPerson`; sets `Attacker/AttackerWeapon/AttackerSkin` (kill feed data); pooled `Factory_Pool.FxHit` at target + up 0.75 - dir*0.5; sfx; one-shot -> `Kill(Killer_Type.Enemy)` unless shielded (shield consumed); else effect + ragdoll force `forward*Power + up*5`; `Taptic.Medium()` for player; `EventCharacterHit` | **Power is knockback force, not HP damage** |

KT weapon asset table (all `Configs/Item/Attack/v1|v2/*.asset`) [V]:

| Weapon (type id) | Rank | Range | Power | Cooldown s | Effect | Notes |
|---|---|---|---|---|---|---|
| Knife default (1) | Normal, free | 3 | 30 | 2.5 | - | base melee |
| Black/Fire/Gambit/Ice knife | Normal/Rare | 3 | 30 | 2.5 | none (poison knife = Effect 3) | cosmetic variants |
| Galaxy knife (9) | Normal | 3 | 30 | 1.5 | - | SpeedMultiplier 1 |
| Rainbow knife (7) | Legend | 3 | 30 | 1.5 | - | `IsOneShot` = true |
| Great Sword (101) | Rare | 6 | 30 | 1.5 | - | long melee |
| Deadly / Freeze sword | Legend | 6 | 15 | 1.5 | Effect 1 (Burning) / 2 (Freeze) | |
| Serahp Blade (8) | Legend | 6 | 30 | 1.5 | - | |
| Bonk (302), Trident (303) | Rare | 5 | 30 | 2.5 | - | |
| Infinity Gauntlet (301) | Normal | 7 | 30 | 2.5 | - | |
| Banana (201) parabola throw | Normal | 10 | 30 | 1.5 | - | |
| Captain Shield (202), Mjolnir (203, Legend), Shuriken (204) linear throw | Rare/Legend/Normal | 15 | 30 | 1.5 | - | |
| Electric Gun (401) projectile | Normal | 30 | 30 | 1.0 | - | pooled bullet |
Pattern: **class (melee 3 / long melee 6 / mid 5-7 / thrown 10-15 / gun 30) sets Range and Cooldown; rarity mostly changes visuals + one-shot/effect, not raw power** [V values; reading is I].

### 2.2 TBE pickaxe + Bonk [V]
- Hotbar `Egg_Hotbar` (static, `enum Hotbar_Tool {Axe, Bonk, Pet, PetSecond, PetThird}`), keys 1-5, `Select/CanSelect`, `EventChanged`, statics reset with `RuntimeInitializeOnLoadMethod(SubsystemRegistration)`; empty slot falls back to slot 0 (`TBE S/Logic/Egg/UI/Egg_Hotbar.cs`).
- Swing: `SAB_Character_Dig.TryDig()` gates (busy, treadmill training, `IsAxe`, a target exists for the player) -> `Animator.TriggerDig(DigSpeed 1.5)` -> `Tween.Delay(clip/speed * 0.88)` -> `OnImpact` posts `Event_SAB_Dig_Hit` (hit logic lives elsewhere) (`SAB_Character_Dig.cs`, `Factory_SAB.cs`).
- Target: `Egg_Pickaxe.FindTarget` loops the static `Egg_Static.ActiveEggs` list, squared planar distance vs `HitRange 4.3 + egg.Radius`, picks nearest; one swing damages exactly one egg; highlight outline refreshed every 0.2 s; `Factory_Egg.HitConeAngle` 140 exists but the nearest-target path does not check facing [V code comment "no facing check"].
- Auto dig: rewarded `Monet_AutoHit`, polled every 0.12 s, only swings when a target is in reach.
- Bonk (melee vs characters): range 3.2 m, half angle 70 deg, cooldown 0.55 s (or swing duration, whichever longer), knock force 10, no use inside the boss safe zone (`Character_Bonk.cs`); reaction = `Character_Knock` physical ragdoll built at runtime from 9 named bones, up impulse 5.5, lie 1.6 s, stand-up blend 0.55 s [V `Character_Knock.cs`].

### 2.3 Melee vs ranged vs thrown (KT)
| Kind | Class | Numbers | Source |
|---|---|---|---|
| Melee | `Character_Attack` overlap + cone + delayed `OnHit` | see 2.1 | [V] |
| Linear throw (shield, hammer, shuriken) | `Item_Throw_Linear` | speed 12, maxDistance 12 (overridden by weapon Range), collision radius 0.15, optional overlap mode + unstoppable, spin 360 deg/s, pooled via `PoolPrefabConfig`, `FixedUpdate` step | [V `Item_Throw_Linear.cs`] |
| Parabola throw (banana) | `Item_Throw_Parabola` | throwSpeed 15, jumpPower 1, targetYOffset 0.5, predictionForwardBias 0.25, lifetime 4 s, warning 1 s with 4 blinks then explode fx | [V] |
| Gun | `Item_Gun` -> `Item_Gun_Projectile` | speed 50, lifetime 4 s, range-based release, `OnCollisionEnter`, hit vfx pooled, owner collider ignored; **aims at target only when owner is player** | [V] |
Target pick for throws: best front-dot, tie broken by nearest (`SelectThrowTarget`). Held item hides on throw and re-shows after `Cooldown` [V].

---------------------------------------------------------------------------
## 3. Mining, pickaxe tiers, dig and bomb modes

### 3.1 TBE pickaxe tiers (egg damage) [V `TBE S/Logic/Egg/EggBalanceFormula.cs`, `Configs/Egg/Pickaxe_Asset.cs`]
Power per tier (x4 ladder of the reference shop): `1, 4, 15, 60, 250, 1k, 4k, 15k, 60k, 250k, 1M, 4M, 15M, 60M, 250M` (15 tiers).
Price per tier: `0, 200, 1k, 5k, 25k, 120k, 620k, 3.1M, 16M, 78M, 390M, 2B, 9.8B, 49B, 240B`, then `RoundNice` snaps mantissa to {1,1.2,1.5,2,2.5,3,4,5,6,8,10}. Price/power ratio first-tier 200:4 = 50, last 240B:250M = 960 (cost grows faster than power, payback kept by income) [V values, ratio is I].
Recommended tier per zone: `1 + round((zone-1) * 1.4)` -> zones 1..11 map to tiers 1,2,4,5,7,8,9,11,12,14,15.
Egg HP: `NominalHp = PickaxeDamage(RecommendedTier(zone)) * hitsToBreak`, rolled with variance x0.9..1.1. Hits to break by rarity: `4,6,9,14,20,28,40,56,80,112`. Spawn weights: `40,25,15,10,6,3,1,0.6,0.3,0.12`. Break threshold: `hp < 1` counts as broken (display is integers).
`Pickaxe_Asset` fields: tier, name, damage, price, skinPrefab (hand model), icon, 3 aura colors + rainbow flag, 2 `ToolFxLayer` (material, colors, rate/size/speed/gravity, orbit/grow/spin), `Shop_Purchase` (Money/IAP), rarity from a table `RARITY_BY_TIER` (Common x2, Uncommon x2, Rare x2, Legendary x4, Divine x2, Cosmic x2, Secret) [V].
Egg hit feedback: scale punch `(0.18,-0.22,0.18)*scale` 0.22 s, rotation shake z 9 deg 0.25 s, world HP bar hidden at full and hidden after break, floating text `-damage` red 1.0 scale vs break gold 1.25 scale, duration 0.75 s rise 1.6 m, `Game_Haptics.Light()` on break, FOV punch +12 (out 0.18 s, back 0.45 s) when a pet is delivered [V `Egg_Node.cs`, `Egg_FloatingText.cs`, `Egg_ScreenFx.cs`].
Event flow: `Event_SAB_Dig_Hit(Character)` -> `Egg_Pickaxe` -> `Egg_Node.ApplyDamage` -> `Event_Egg_Hit(egg, damage, broke, position)` (floating text, haptics) / `Event_Egg_BreakStarted` [V].
Bots use `bot.PickaxeDamage` through the same path [V]. TBE has **no terrain deformation**: the "pickaxe" damages nodes.

### 3.2 CT dig and bomb modes (real terrain) [V]
- Terrain is the **Digger** plugin (`DiggerMasterRuntime`, `BrushType.Sphere`, `ActionType.Dig`, async edit). `DigController.PerformActualDig(pos, dir)` calls `Digger` with `adjustedDigSize = digSize * MapDigSizeMultiplier`; ground layer probe `SphereCast(radius 0.3, down)` to pick texture/layer (`CT _Game_DigMode/Scripts/Character/Movement/DigController.cs`).
- Dig duration `= baseDigDuration(3 s) / digSpeedMultiplier * MapCooldownMultiplier`, shown by `DigProgressBar`; bomb throw duration `= baseThrowDuration(2.5 s) / throwSpeedMultiplier * MapCooldownMultiplier` (`DigCooldownSystem.cs`, `BombCooldownSystem.cs`). Harder worlds: smaller hole, longer cooldown (`DigMode_World_Config`: `digSizeMultiplier`, `cooldownMultiplier`, `coinMultiplier`).
- Reward: `Base(10) x (petCoin+1) x (toolCoin+1) x MapCoinMultiplier` (`DigRewardCalculator.cs`) via `IRewardStats.GetCoinMultiplier()`.
- Pickaxe tier asset `PickaxeConfig` (37 tiers, fields Power/Speed/Coin multiplier, Cost string, UnlockType, AssetReference): Wood P1.1 S2 C8 cost 0; #2 P1.8 S2.1 C42 100; #3 2.5/2.2/311 2.5K; #4 3.25/2.3/1.1K 35K; #7 5.5/2.6/366K 300M; #10 7.7/2.8/15M 120B; #13 10.7/3.1/354M 6T; #16 12.8/3.35/5.3B 250T; #19 15.25/3.6/113B 35a; #25 19.3/4.2/347T 450b; #31 22.66/4.8/633a; #37 24.4/5.4/5c (suffix-letter big numbers via `UtilsNumber.ParseCompactNumber`) [V assets].
  Reading: Power (hole size) saturates (1.1 -> 24.4, ~log), Speed grows ~+0.1/tier then +0.075, Coin grows ~x3-5 per 3 tiers, cost ~x10-15 per 3 tiers [I from sampled rows].
- Bomb (`BombConfig`, 9 tiers, `Configs/Bombs/Bomb 1..9.asset`): [V]

| Bomb | PowerMult (blast radius x) | ThrowSpeed | Fuse s | CoinMult | Cost |
|---|---|---|---|---|---|
| 1 | 1 | 2.2 | 2 | 2 | free |
| 2 | 1.3 | 2.2 | 2 | 2.5 | 1K |
| 3 | 1.5 | 2.4 | 2.1 | 3 | 7K |
| 4 | 2.5 | 3.5 | 2.7 | 4.1 | 34K |
| 5 | 3 | 4 | 3.2 | 5.7 | 388K |
| 6 | 5 | 4.5 | 4 | 6.8 | 1M |
| 7 | 7 | 6 | 5 | 7.7 | 100M |
| 8 | 8 | 7 | 5.5 | 10 | 2B |
| 9 | 10 | 8.5 | 7 | 14 | 39B |
  Bigger bombs have longer fuse (+0.5..1 s per late tier) as the built-in downside [I].
- Bomb flight: `BombController.SpawnAndThrowBomb` AddForce `VelocityChange`, default direction `(0,0.3,1)`, throwSpeed 10 base, inherits player velocity (`inheritVelocityFactor` 1, `moveBoostScale` 0.5, max inherit 20), `ThrownBomb` explodes after delay, last 0.8 s `flashStartWindow` blink, `RangeDetector` scan (RaycastPro) must find diggable colliders before `PerformExplosion`; blast radius `explosionRadius(3) x config.PowerMultiplier x MapDigSizeMultiplier` (`BombController.cs`, `ThrownBomb.cs`, `BombStatsController.cs`). `ThrownBomb` uses LeanPool + coroutines + `WaitForSeconds` (legacy; replace with `PoolPrefabGlobal` + UniTask).
- Auto modes: `AutoDigController`, `AutoBombController` + buttons; NPC diggers/bombers use a hand-rolled `IBombState` machine (Idle/Wander/Fly) [V file list].

---------------------------------------------------------------------------
## 4. Item data model, rarity, loot

### 4.1 KT `Item_Info` polymorphism [V `KT S/Logic/Item/Info/*`, `Item_Asset.cs`]
- `Item_Asset : ScriptableObject { [SerializeReference] Item_Info _info; }` (Odin-free SerializeReference; subclasses `Item_Info_Weapon`, `_Cape`, `_CoilSpring`, `_SpeedBoost`).
- `Item_Info` base: `_name, _type (Item_Type enum, 1xx swords, 2xx throws, 3xx melee, 4xx gun, 1001+ carpet/jetpack/cape/coil), _rank (Normal/Rare/Legend), _isFree, _thumbnail, _prefab, _subItem, _class (Battle/Support/SupportNoneAttack), _sfxUsed, _sfxHit, Fx_Info[] _fxUsed`. `TryGetInfo<T>`, `TryGetAttackEffect`, `PlayFxUsed/PlayFxHit` (pooled vfx + audio).
- `Item_Info_Weapon` adds `AttackType, Range, Power, Cooldown, SpeedMultiplier, IsMoveLockedWhenAttacking, AttackDuration, IsOneShot, Effect_Type, IncludedWing`.
- `Item_Asset` also wraps runtime unlock rules: permanent vs session vs per-life unlock (`Unlock_Type.FreePerLives`, `UpdatePerLives/UpdatePerSession`), `Lock()` re-equips default if the equipped item is locked, events `Event_Item_Locked/Unlocked/Equipped`.
- `Factory_Item : SerializedScriptableObjectSingleton` holds `Item_Asset[] _configs` (`[AssetList(Path="_Game/Configs/Item/")]`), `_default`, `_carpet`, `_frameByRank`, builds `Dictionary<string,..>` and `Dictionary<Item_Type,..>` in `OnInitialize`.
- Persistence: `Data_Item : DataBlock` with `Dictionary<string, Item_Data{_isUnlocked,_isUnlockThisSession}>`, `DataValue<string> Equipped, EquippedBuff`; `Get(ID)` uses `TryAdd` lazily [V].
Weakness: weapon behavior is chosen by `switch (Item_Type)` in code, not by the data class; a data-driven design should let the info class own `Execute` (see section 10).

### 4.2 Rarity systems found [V]
| Project | Enum | Count | Use |
|---|---|---|---|
| KT `Item_Rank` | Normal, Rare, Legend | 3 | weapon frame sprite (`Factory_Item._frameByRank`) |
| KT `Rarity_Type` + `Rarity_Asset{Color, FxShiny}` | Common..Mythic | 6 | pets/gacha; `Rarity_Randomizer` uses **money bands** (`_moneyFrom/_moneyTo` -> `Rarity_Randomizer_Data{Rarity, Rate 0..1}[]`) so odds shift with the player's wealth |
| TBE `Egg_Rarity` | Common..Celestial | 10 | hits-to-break, spawn weight, income multiplier `1, 2.5, 6, 16, 39, 98, 240, 610, 1600, 4200` (~x2.5 per step then x2.6-x2.7), frame sprite per rarity, `Rarity_Fx` aura |
| CT `RarityType` | in chest reward | - | `ChestDataSO.Reward {Type, Rarity, UnlockChance 0..1, Value, Pet/Pickaxe/Bomb ref}` |
Rarity color/frame/fx belong in one `Rarity_Asset` table; stat power should come from the tier ladder, not the rarity enum [I].

### 4.3 Loot and drop tables [V]
- KT gacha: `Gacha_Box_Asset { Gacha_Box_Reward[] {Item_Asset, float Weight}, price }`; `RollItem()` = sum weights, `Random.value * total`, cumulative scan; `GetPercent(item)` for the displayed odds.
- TBE egg luck: `LUCK_VALUES {1,2,3,5,10,25,50,100,500,1k,5k,10k,100k,1M}` with weights `{45,25,14,7,4,2.5,1.3,0.7,0.3,0.12,0.05,0.02,0.005,0.001}`; higher-rarity eggs lean the weights (`lean = 1+rarity*0.08`); luck buys at most 4 visual rarity steps but only 2 count for income. Mutation odds at luck 0: Normal 88 / Gold 9 / Diamond 2.5 / Rainbow 0.5 (%); luck 1 triples specials. Size roll bell curve in [0.8, 1.4].
- ME boost shop: per-rank restock weights (base vs VIP set), stock ranges per rank, `maxStock` 10, fuse 3 items -> 1 higher (`Boost_Fuse.FuseSlotCount = 3`) [V `ME S/Logic/Shop/Boost/*`].
- CT chest: list of rewards with `UnlockChance` and open timer `OpenDurationSecond`, ads or currency price [V].
- Kill rewards: KT none found. TBE reward is the egg's pet (income per second), plus money from deposits; CT is currency per dig/bomb via the formula in 3.2.

---------------------------------------------------------------------------
## 5. Inventory, hotbar, equipment slots

| Concern | Implementation | Source |
|---|---|---|
| Backpack list UI | KT `Item_Inventory` popup: iterates `Factory_Item.Configs`, instantiates `_itemPrefab` for unlocked ones into a `ScrollRect.content`, `Item_Inventory_Selection.Init(config)`; closes on player death (StaticBus) | [V] |
| Hotbar | TBE `Egg_Hotbar` (5 slots, static state, `EventChanged`), `Egg_HotbarUI` slot widgets and `Character_PickaxeSkin` held model react to the event; pet slots map to `Data_Egg.PetAtHotbarSlot(slot)` | [V] |
| Two equip classes | KT `Item_Class.Battle` vs `Support`: `Data_Item.Equipped` and `EquippedBuff` | [V] |
| Held visual | KT toggles pre-baked children (`Item_Activator`); TBE swaps `Pickaxe_Asset.SkinPrefab` on `Character_PickaxeSkin`; both keep the model out of save data | [V] |
| Cosmetic slots | skin, wing (`Wing_Asset` + `Data_Wing`), aura/trail (`Aura_Provider`: `Dictionary<Asset, GameObject>` pre-baked on skin), pet (`Pet_Updater` static registry), cape/coil as items | [V] see `04-gameplay-actors.md` s.9 |
| Stat layers | `Character.Controller.MoveSpeedMultiplier += weapon.SpeedMultiplier` on equip, `-=` on release; coil `JumpVerticalMultiplier`, `FallGravityMultiplier = 1-FallDecreaseRate` | [V `Character_Item.cs`] |
| Persistence | `Data_Item` (KT), `Data_Egg._pickaxeEquipped DataValue<int>` + `_pickaxeOwned List<int>` clamped on Init (TBE), `DataBomb.Current/Best` (CT) | [V] |
| Locking rules | free / per-life / per-session / permanent; `Lock()` falls back to default item | [V] |
Bag capacity: TBE `ExtraSlotPrice(n) = 500 * 3^n` (pet bag) [V]; no weapon-count cap in any project.
Missing everywhere: drag-and-drop reorder, stack counts for tools, durability. Treat as new design.

---------------------------------------------------------------------------
## 6. Combat feedback ("game feel") [V unless noted]
| Hook | Value | Source |
|---|---|---|
| Camera shake | `CameraShaker.Shake(amp 0.4, freq 3.5, dur 0.2)` default; boss/fall use 0.6/4/0.3, 0.3/3/0.15; fall shake `clamp(...)*5` over 0.4 s | `KT S/Logic/Camera/CameraShaker.cs`, `Character.cs` L795 |
| Camera FOV punch | +12 deg, out 0.18 s, back 0.45 s | `Egg_ScreenFx` |
| Scale punch on hit | `(0.18,-0.22,0.18)` 0.22 s, elasticity 8; rotation shake z 9 deg 0.25 s | `Egg_Node.PlayHit` |
| Haptics | `Taptic.Medium()` on player hit/kill (KT), `Game_Haptics.Light()` on egg break (TBE) | |
| Floating damage | TBE: world-space text pool, rise 1.6 m, 0.75 s, colors red/gold; CT: `TextDamage` pooled prefab, live 3 s, normal color (1,0.4,0.4), critical (1,0.84,0), critical sprite, DOTween sequence, returns to `PoolPrefabGlobal` | `Egg_FloatingText.cs`, `CT CFramework/.../TextDamage.cs` |
| HP bar | TBE `Egg_HpBar` 2 sliced SpriteRenderers, width 1.6 height 0.2 pad 0.05, hidden at >= 0.999; CT `HealthBar` red bar delay 0.1/0.1 s plus yellow trailing 0.5 s, scale-up 1.2 for 0.25 s on change; KT boss bar = UI `Image.fillAmount` + threshold lines | |
| Hit fx/audio | pooled `FxHit`, `AudioConfig` per weapon (`SfxUsed`, `SfxHit`), attackable-target indicator `Fx.SetAttackableActive` | |
| Impact timing | impact at normalized 0.88 of swing clip (TBE) / 0.35 s after press (KT 0.1+0.25) | |
| Hit-stop | **not implemented** in any read project [V grep]; proposal 0.05-0.08 s `Time.timeScale` dip or animator speed 0 [I] | |
| Death/respawn | KT revive delay 2 s, ragdoll 2.5 s, revive shield `ReviveProtectDuration`; TBE knock lie 1.6 s + stand 0.55 s; egg respawn 3-6 s | |

---------------------------------------------------------------------------
## 7. Enemies, bosses, status effects

### 7.1 KT status effects [V `Character_Effect.cs`, `Factory_Effect`]
`Effect_Type {None, Burning(1), Freeze(2), Poison(3)}`, one active effect (`DataValue<Effect_Type>`). Priority: Burning blocks Freeze/Poison. Durations from `Game.Factory_Effect.asset`: burn-to-kill delay **1 s** (kills unless shielded), freeze **4 s** (code default 8; character state `Freeze`), poison **10 s** (code default 5; inverts input, AI too). Each effect has its own `CancelToken`; cleared on death/revive; UI icon + remaining-time via `Character.UI.ShowEffect(type, remain)` updated every 0.1 s. Applied by weapon `Effect` field (knife poison, sword burning/freeze).
Shield: `SetShield(duration)` (revive protect), `SetPermanentShieldEnabled`; one-shot and burning respect `IsShielded`.
Boosters: `Booster_Asset {Booster_Type JetPack/Shoes, Addressable prefab, duration}`, jetpack power 30 / 3 s / refuel 1 s (see doc 04), coil +1 jump multiplier, wing x2 jump multiplier, shop boost `_boostValue 5` with `maxStock 10`, fuse x3 [V].
CT has a reusable `Stat` module: `StatController`, `IStatModifier {StatId, SourceId, Type(Flat/Percent/FlatOverTime/PercentOverTime), Value, IsExpired}` with save data; this is the cleanest buff/stat layer found (SourceId makes removal exact) [V `CT CFramework/Modules/Stat/*`]; not present in SketchEngine package [V doc 01].

### 7.2 Enemy AI attack patterns [V]
- KT bots: attack probability `AIProbAttackPlayer` 0.25, in battle area 0.25, ranged chance `ParkourRangedWeaponChance` 0.15, `AttackRangeOverlapse` 5 (`Factory_AI`); bot weapons picked from `Item_Static.AvailableItems` with ranged/non-ranged weighted buckets (`RangedWeaponWeight`); AI range multiplier `GameStatic.AIAttackRangeMultiplier`; `AI_Attack` calls `Character.Attack.Attack()` (64 lines) [V catalog 04 s.5, `Item_Static.cs`].
- TBE guardian `Boss_Guardian` states `Sleep, Reaction, Chase, Attack, Return, Patrol`; ticked by one `Boss_Manager.Update`; `Factory_Egg`: tick 0.2 s, move 4.2 m/s, chase/wake radius 14, catch radius 1.8, stun 4 s, reaction 0.9 s, attack windup 0.35 s; per-biome `MonsterCombatConfigSO`: attackRange 4 (Desert) .. 10 (Cosmic), cooldown 0.1, windup 0.1, travel speed x2.1..x2.5, `requiredSpeedMultiplier` 0.83..0.95 (chase rule = player speed x boost / egg weight vs boss speed x this) [V].
- KT SpeedKeyboard boss event `SKB_MinigameEvent_Boss`: **HP% phases** (`GetBossPhase`): phase 0 above 0.66, phase 1 <= 0.66, phase 2 <= 0.33; `Event_SKB_MinigameEvent_BossPhaseChange(phase, hp%)` posted only on change from `SceneManager` loop. Phase 1: bot explosion hitbox (delay 2 s), mini-bosses spawn every 5-10 s, count 3, lifetime 10 s, shake 0.6/4/0.3 on slam; phase 2: bot destroyed, boss moves + instant-kill hitbox (`_instantKillHitbox`); HP bar draws threshold lines [V `SKB_MinigameEvent_Config.cs`, `_Boss.cs`, `_BossHpBar.cs`].
- ME boss: patrol speed 2, chase 4, patrol rect X 1 Z 0.5, kill on contact via `OptCollisionRegister` (doc 04 s.6).

---------------------------------------------------------------------------
## 8. Pooling, collision dispatch, performance (as found)
- Pool: `PoolPrefabGlobal.Get(PoolPrefabConfig)` / `Release(config, go)`; configs exposed by `Factory_Pool` (`FxHit`, `FxShield`, `FxAttackWave`); projectile prefabs carry `PoolPrefabItem` and release on hit/range [V KT]. CT used LeanPool + `PoolPrefabGlobal` mix [V].
- Characters are found from a collider by `OptScriptLookup.TryFindFirst<Character>(collider, out c)` (dictionary by instance id) in melee fallback and projectiles [V]. TBE avoids physics: static lists (`Egg_Static.ActiveEggs`, `Character_Knock.All`), `Update` throttled to 5 Hz for highlight [V].
- Frame budget habits worth copying: one `Boss_Manager.Update` for all bosses, `Character.EventTick` re-broadcast, `_overlapBuffer` 32, attackable-check interval 0.15 s. To avoid: per-tick `new HashSet<Character>()` and `new List<Character>()` in `Character_EventTick` [V alloc evidence].

---------------------------------------------------------------------------
## 9. Cross-project comparison
| Topic | KT | TBE | CT |
|---|---|---|---|
| Damage model | knockback + one-shot/kill, no HP | double HP on eggs, damage = pickaxe tier | no HP; dig size/reward formulas |
| Tool data | `Item_Asset` + `[SerializeReference] Item_Info` | flat `Pickaxe_Asset` (15 tiers) | flat `PickaxeConfig` (37), `BombConfig` (9) |
| Hit detection | overlap/detector snapshot + cone, delayed | nearest-in-list, impact event at 0.88 | terrain brush; `RangeDetector` for bombs |
| Slots | Battle + Support equip classes | hotbar 5 | current pickaxe + current bomb |
| Upgrade | buy/unlock tiers via gacha/IAP/ads | price ladder + formula, bots mirror | cost string ladder, 37 tiers |
| Events | StaticBus Item_* | StaticBus Event_SAB_Dig_Hit/Event_Egg_Hit | StaticBus Event Bomb*/Pickaxe* |
| Frameworks | CodeSketch | SketchEngine | CFramework |

---------------------------------------------------------------------------
## 10. DESIGN - generic Tool + Combat + Inventory skeleton (SketchEngine house style)
Rules: first-party code in `namespace Game`, folders per AGENTS.md, no new persistence layer, no parallel FSM/bus/pool. Before coding inspect the installed framework (CodeSketch `OptCollisionRegister<T>` vs SketchEngine non-generic with `owner is T`).

### 10.1 Folder layout
```
Assets/_Game/
  Configs/Tool/        Tool_Pickaxe_01.asset ... Tool_Sword_01.asset, Tool_Bomb_01.asset
  Configs/Combat/      Status_Burn.asset, Loot_Table_*.asset, Rarity_Table.asset
  Configs/Audio/Tool/  per tool AudioConfig
  Prefabs/Tool/        held models, projectiles, bombs, fx
  Resources/SketchEngine/ScriptableObjectSingletons/   Game.Factory_Tool.asset, Game.Factory_Combat.asset, Game.Factory_Loot.asset
  Scripts/Data/        Data_Inventory.cs
  Scripts/Factory/     Factory_Tool.cs, Factory_Combat.cs, Factory_Loot.cs
  Scripts/Event/Tool/  Event_Tool_*.cs   Scripts/Event/Combat/ Event_Combat_*.cs   Scripts/Event/Inventory/
  Scripts/Logic/Tool/  Tool_Asset, Tool_Behavior*, Tool_User, Tool_Hotbar, Tool_Held, State/Tool_State_*
  Scripts/Logic/Combat/ IDamageable, Combat_Health, Combat_Target, Combat_Resolver, Combat_Status, Combat_Projectile, Combat_Bomb, Combat_Fx
  Scripts/Logic/Inventory/ Inventory_Panel, Inventory_Slot_UI, Hotbar_UI
```
Singleton asset path for SketchEngine confirmed as `Resources/SketchEngine/ScriptableObjectSingletons/` [V doc 01]; verify the exact file naming in the target project before creating.

### 10.2 Data records (persistent, scene-free) in `Data_Inventory : DataBlock<Data_Inventory>`
| Field | Type | Note |
|---|---|---|
| `_tools` | `Dictionary<string, Tool_Record>` | `Tool_Record {bool Owned; int Level; int Kills/Uses (optional)}`; lazy `TryAdd` |
| `_equipped` | `DataValue<string>` | current held tool id (for single-slot games) |
| `_hotbar` | `List<string>` (fixed N from Factory) | slot -> tool id, empty = "" |
| `_selectedSlot` | `DataValue<int>` | session-safe default 0 |
| `_loadouts` | `Dictionary<Equip_Slot, string>` | cosmetic slots (hat/aura/trail/wing/pet) by id |
| `_boosters` | `Dictionary<string, int>` | stock count, cap from asset |
`Init()`: `base.Init(); _tools ??= new(); _hotbar ??= new(); ...`; clamp owned/equipped to registry like `Data_Egg.Init`; give the default free tool. No scene objects, no assets stored, only ids.

### 10.3 Config SOs
- `Tool_Asset : ScriptableObject` (id, display name, `Tool_Kind` (Melee/Mine/Ranged/Thrown/Support), `Rarity_Type`, icon, held prefab, `Tool_Stats` struct, `[SerializeReference] Tool_Behavior _behavior`, `Tool_Upgrade` block, audio/fx refs, purchase `Shop_Purchase`, tier int).
- `Tool_Stats` struct: `Damage, Cooldown, Range, ConeHalfAngle, ImpactNormalized (0..1), SwingSpeed, Knockback, CritChance, CritMultiplier, MoveSpeedMultiplier, MaxTargets`.
- `Tool_Behavior` (abstract, SerializeReference subclasses): `Tool_Behavior_Melee {ConeCheck, TargetLayer}`, `_Mine {NodeTag, DamageToNodesOnly}`, `_Projectile {PoolPrefabConfig, Speed 50, Lifetime 4, Pierce}`, `_Thrown {arc, FuseSeconds, BlastRadius, Falloff, PoolPrefabConfig}`. Each exposes `bool TryExecute(Tool_Context ctx)`; the data class owns the algorithm (fixes KT's `switch (Item_Type)`).
- `Tool_Upgrade {double BaseDamage; double DamageGrowth (x4 or 1.97); double PriceBase; double PriceGrowth (2.05); int MaxLevel; bool SnapNice}` plus `Tool_Upgrade.Damage(level)`, `.Price(level)` using `RoundNice` ladder (see EggBalanceFormula).
- `Status_Asset {Status_Type, Duration, TickInterval, TickDamage, StackRule (Refresh/Ignore/Replace), Priority, BlocksStatuses[], Icon, Fx}`.
- `Loot_Table {Entry[] {Asset, Weight, MinRarity}, Rolls, PityAfter, GuaranteedRarity}`; `Rarity_Table` (Color, FxShiny, Frame, StatMultiplier).
- `Boss_Phase_Config {float[] HpThresholds (0.66, 0.33), per-phase Status/Speed/Attack overrides}` reused from KT `SKB_MinigameEvent_Config`.

### 10.4 Factories (read-only static surface, caches built in `OnInitialize`)
- `Factory_Tool : ScriptableObjectSingleton<Factory_Tool>`: `Tool_Asset[] _tools`, `_default`, `_hotbarSize (5)`, `_defaultHitLayer`, `_hitFxPool`, `_floatingTextPool`; dictionaries by id; duplicate/missing-id validation; `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)] ResetStatics()` (TBE does this, KT does not).
- `Factory_Combat`: `HitStopSeconds`, `RagdollSeconds 2.5`, `ReviveDelay 2`, `ReviveShield`, `CritColor`, `DamageNumberDuration 0.75`, `DamageNumberRise 1.6`, `ShakeAmp/Freq/Duration`, `OverlapBufferSize 32`, `AttackableCheckInterval 0.15`, `FriendlyFire false`.
- `Factory_Loot`: tables by id, global luck, rarity weights.

### 10.5 Events (StaticBus, `IEvent`, constructor-supplied payload)
`Event_Tool_Equipped(Actor, Tool_Asset)`, `Event_Tool_Unequipped`, `Event_Tool_Used(Actor, Tool_Asset)`, `Event_Tool_Upgraded(Tool_Asset, level)`, `Event_Hotbar_Changed(slot, Tool_Asset)`, `Event_Combat_Hit(Attacker, Target, DamageInfo, bool killed, Vector3 popupPos)` (mirrors `Event_Egg_Hit`), `Event_Combat_Dead(Target, Killer, DamageInfo)`, `Event_Combat_PhaseChanged(Boss, phase, hp01)`, `Event_Combat_StatusChanged`, `Event_Loot_Dropped(Table, Entry, Vector3)`, `Event_Inventory_Changed`. Local one-to-one things stay C# events (`Combat_Health.EventChanged`, like `Character.EventDead`). Subscribe in `OnEnable`, unsubscribe in `OnDisable`.

### 10.6 Runtime classes (list)
| Class | Base | Responsibility |
|---|---|---|
| `Tool_User` | `MonoCachedHub<Actor>` | owns the `StateMachine<Tool_State>`; `TryUse()`; reads equipped tool; cooldown; move-lock; bots call the same API |
| `Tool_State` enum + `Tool_State_Idle/Windup/Impact/Cooldown` | `IStateMachine` | Windup waits to `ImpactNormalized` of the clip then posts to behavior; Cooldown shows HUD fill |
| `Tool_Held` | `MonoCachedHub<Actor>` | swaps pre-baked held model/fx on `Event_Tool_Equipped` (provider dictionary pattern) |
| `Tool_Hotbar` | `MonoCached` + static | slots, `Select/CanSelect`, keyboard 1-5, resets statics, falls back to slot 0 |
| `Combat_Health` | `MonoCachedHub<Actor>` : `IDamageable` | `DataValue<double> Hp`, max, regen, shield, `ApplyDamage(in DamageInfo)`, posts events, `HpBar` update; double for big-number games |
| `DamageInfo` | struct | `Amount, Source, Tool, Knockback, Point, IsCrit, StatusId, Kind` |
| `Combat_Target` | `OptCollisionRegister` + registry | registers colliders for projectile lookup and adds itself to a static `Combat_Target.All` list for non-physical queries |
| `Combat_Resolver` | static | `FindInCone(origin, fwd, range, halfAngle, buf)` (squared distance + dot, list or `OverlapSphereNonAlloc`, layer mask, `QueryTriggerInteraction`), `FindNearest`, friendly-fire filter |
| `Combat_Projectile` | `MonoCachedFast` pooled | FixedUpdate step, range/lifetime release, sensor owner uses `OptCollisionLookup.TryFindFirst<IDamageable>` (SketchEngine) / `OptCollisionRegister<T>` (CodeSketch) |
| `Combat_Bomb` | pooled | fuse timer via `Tween.Delay` or UniTask with cancel, blink last 0.8 s, `Physics.OverlapSphereNonAlloc` blast, falloff, terrain hook `IDigTerrain.Dig(pos, radius)` (optional Digger adapter) |
| `Combat_Status` | `MonoCachedHub<Actor>` | per-status `CancelToken`, priority/block rules, UI update every 0.1 s, cleared on dead/revive |
| `Combat_Phases` | `MonoCached` | HP% thresholds -> `Event_Combat_PhaseChanged` only on change |
| `Combat_Fx` | static | pooled hit fx, floating number (pooled), shake, FOV punch, haptic, optional hit-stop |
| `Loot_Roller` | static | weighted roll (KT `RollItem`), luck/rarity step, pity counter, `GetPercent` for displayed odds equal to real odds |
| `Inventory_Panel`, `Hotbar_UI`, `Inventory_Slot_UI` | UI | scroll list of owned tools, slot widgets bound to `Event_Hotbar_Changed`; no per-frame text rebuild |
| `Tool_Upgrade_Service` | static | price/level math, spend via existing currency data, posts `Event_Tool_Upgraded` |

### 10.7 Flow (one use)
`Input -> Tool_User.TryUse()` -> state Windup (trigger anim `SwingSpeed`) -> `Tween.Delay(clip/speed * ImpactNormalized)` -> state Impact -> `behavior.TryExecute(ctx)` (resolver finds targets) -> `target.ApplyDamage(DamageInfo)` -> `Combat_Health` posts `Event_Combat_Hit` -> consumers: floating text, hit fx, haptic, shake, bar; on kill `Event_Combat_Dead` -> `Loot_Roller` -> `Event_Loot_Dropped` -> currency spread fx. State Cooldown for `Cooldown`, HUD fill from `Tool_User.CooldownNormalized`.

### 10.8 Worked examples (3 tools)
Numbers marked [V] come from the projects above; others are initial tuning [I] to be validated by `playmode-script-testing` / the balance simulation tools (TBE `Balance_UpgradeLoopSimulation` pattern).

**A. Pickaxe (Mine behavior, tiered)** `Tool_Pickaxe_01..15`
| Field | Value | Source |
|---|---|---|
| Kind / behavior | Mine / `Tool_Behavior_Mine` (nearest node in range, one target per swing) | [V TBE] |
| Range | 4.3 m + node radius | [V `Factory_Egg._hitRange`] |
| Cone | none (nearest, no facing) | [V] |
| Swing | speed 1.5, impact normalized 0.88 | [V] |
| Damage by tier | 1, 4, 15, 60, 250, 1k, 4k, 15k, 60k, 250k, 1M, 4M, 15M, 60M, 250M | [V] |
| Price by tier | 0, 200, 1k, 5k, 25k, 120k, 620k, 3.1M, 16M, 78M, 390M, 2B, 9.8B, 49B, 240B | [V] |
| Node HP | `Damage(recommendedTier) * hits * U(0.9,1.1)`, hits 4..112 by rarity | [V] |
| Feedback | scale punch 0.22 s, rot shake 0.25 s, floating red/gold, haptic light on break | [V] |
| Terrain option | `IDigTerrain` adapter, radius `base * PowerMultiplier * worldSize`, dig time `3 s / speed * worldCooldown` | [V CT] |
Hotbar slot 1, held-model aura color per tier, upgrade path = buy next tier (TBE) or `Level` growth `x1.97/level` (`DAMAGE_GROWTH 1.9695` = 10 ^ (1/ (1.4 tiers/zone *...)) [V constants]).

**B. Sword (Melee, cone)** `Tool_Sword_Great`
| Field | Value | Source |
|---|---|---|
| Behavior | `Tool_Behavior_Melee`, `MaxTargets` 8, ignore self/friendly | [I] |
| Range | 6 m (KT Great Sword), short knife 3 m, Bonk 3.2 m | [V] |
| Cone half angle | 90 deg (KT) or 70 deg (TBE Bonk) | [V] |
| Cooldown | 1.5 s (KT sword) vs 0.55 s (TBE Bonk) | [V] |
| Impact delay | 0.25 s after swing start (KT) or 0.88 of clip (TBE) | [V] |
| Damage (HP game) | proposed 30 base; KT `Power 30` is knockback force | [V/I] |
| Knockback | `forward*Power + up*5` (KT), TBE force 10 + up impulse 5.5 | [V] |
| Hit reaction | ragdoll 2.5 s (KT) / lie 1.6 s + stand 0.55 s (TBE) | [V] |
| Effects | optional `Status_Burn` (1 s kill delay) / `Status_Freeze` (4 s) / `Status_Poison` (10 s) | [V] |
| Crit | 5% x2 (not in references) | [I] |
| Feedback | pooled hit fx at target+0.75 up, `Taptic.Medium`, shake 0.4/3.5/0.2, optional hit-stop 0.06 s | [V/I] |
| Move lock | `AttackDuration` 0.25 s optional | [V] |

**C. Bomb (Thrown, AoE, optional terrain)** `Tool_Bomb_01..09`
| Field | Value | Source |
|---|---|---|
| Behavior | `Tool_Behavior_Thrown`: arc `(0,0.3,1)` dir, speed `10 + inherit*0.5`, `VelocityChange` | [V CT] |
| Fuse | table in 3.2 (2 s .. 7 s), blink last 0.8 s | [V] |
| Blast radius | `3 * PowerMult` (1..10) times world size | [V] |
| Cooldown | 2.5 s `/ ThrowSpeed` (2.2..8.5 per tier in CT) | [V] |
| Cost | free, 1K, 7K, 34K, 388K, 1M, 100M, 2B, 39B | [V] |
| Reward mult | 2, 2.5, 3, 4.1, 5.7, 6.8, 7.7, 10, 14 | [V] |
| Combat damage | `Damage * falloff(d/r)`, falloff linear 1 -> 0.3 | [I] |
| Safety | bomb never hits owner unless `SelfDamage`; one explosion flag; return to pool after 1 s fx | [V flag `hasExploded`] |
| Pooling | `PoolPrefabGlobal`, not LeanPool/coroutines | house rule |

### 10.9 Tuning table (cheat sheet of found numbers)
| Parameter | Value | Source |
|---|---|---|
| Melee short / long / bat / thrown / gun range | 3 / 6 / 3.2-5 / 10-15 / 30 m | KT, TBE |
| Cooldown melee / long / thrown / gun | 2.5 / 1.5 / 1.5 / 1.0 s | KT |
| Hit delay (KT) | 0.25 s (0.1 carpet); fx at +0.1 s | KT |
| Attack check interval / overlap buffer | 0.15 s / 32 | KT |
| Pickaxe hit range / cone / respawn | 4.3 m / 140 deg / 3-6 s | TBE |
| Ragdoll duration | 2.5 s (KT), 1.6+0.55 s (TBE) | |
| Effect durations | burn kill 1 s, freeze 4 s, poison 10 s | KT |
| Boss HP phase thresholds | 0.66, 0.33 | KT |
| Boss chase tick / move / wake / catch / stun | 0.2 s / 4.2 / 14 / 1.8 / 4 s | TBE |
| Projectile speed / life / hit radius | 50 / 4 s / 0.15 (thrown 12 m/s, 12 m) | KT |
| Damage text duration / rise | 0.75 s / 1.6 m (CT live 3 s) | TBE, CT |
| Tier growth | x4 power, ~x2 price tier (x2.05 formula), hits 4->112 | TBE |
| Income per rarity | x2.5 then x2.6 per step | TBE |

### 10.10 Wiring checklist (done-means-wired)
Create assets via Unity (MCP or editor tool, never hand YAML): `Factory_*` singleton assets in Resources path; tool assets in `Configs/Tool`; held prefabs and pool configs; wire `Tool_User` + `Combat_Health` + `Combat_Target` on the actor prefab (source prefab, not scene override); HUD attack button + cooldown image + hotbar slots; layer mask for attackable; verify the collision matrix; compile, check Console, EditMode tests for formula/roll/upgrade (pure static functions are testable), PlayMode test: equip -> swing -> hit -> kill -> loot -> save/load.

---------------------------------------------------------------------------
## 11. Risks and open items
- KT `Character_Attack` internals partly skimmed (L1-696 read, `AI_Attack.cs` only by catalog); `Character_UI` nametag/health UI not located; TBE `Egg_HotbarUI`, `Character_PickaxeSkin`, `Boss_Guardian` internals not read line by line; CT `StatController` implementation not read (interface/modifiers only).
- No Profiler/device data; no Unity MCP session, nothing compiled.
- KT/TBE use `try{}catch{}` around subscriptions and per-tick allocations; do not clone.
- Displayed vs real odds: luck table and `Rarity_Randomizer` should expose `GetPercent` and tests asserting equality (see catalog jackpot risk).
- HP-based player combat has no reference; numbers marked [I] are proposals to be tuned with a simulation tool (pattern: TBE `Balance_*Simulation`).

---------------------------------------------------------------------------
## 12. Proposed classification

| # | Candidate | Class | Proposed name | Must contain (3-6) |
|---|---|---|---|---|
| 1 | Tool/weapon pipeline | **RECIPE** | `tool-weapon-pipeline` | `Tool_Asset` + `[SerializeReference] Tool_Behavior`; `Tool_User` state machine (Idle/Windup/Impact/Cooldown); impact at normalized clip time (0.88) ; cooldown HUD fill; same API for bots; held visual provider dictionary |
| 2 | Combat resolver rules | **RULE** | `combat-hit-detection-rule` | no per-frame weapon collider; NonAlloc overlap buffer 32 + layer mask + `QueryTriggerInteraction`; squared range + cone dot; static target list for non-physical queries; projectiles use collider sensor + `OptCollisionLookup`; no allocations in the check |
| 3 | HP/damage/status layer | **RECIPE** | `combat-health-status` | `IDamageable` + `DamageInfo`; `Combat_Health` events; status priority/block rules + `CancelToken`; shield/one-shot; death/respawn delay 2 s; HP-phase boss events (0.66/0.33) |
| 4 | Tool tiers and upgrade math | **DATA** | `docs/data/tool-tier-tuning.md` (+ `tool-balance-formula` template) | x4 power ladder + price ladder + `RoundNice`; hits-to-break/weights per rarity; CT pickaxe/bomb tables; reward formula `Base x (pet+1) x (tool+1) x map`; bot mirrors player tier |
| 5 | Hotbar + inventory UI | **RECIPE** | `hotbar-inventory` | static `Tool_Hotbar` with `EventChanged` + SubsystemRegistration reset; `Data_Inventory` shape (dictionary + equipped + hotbar list, clamp on Init); scroll panel of unlocked items; slot-fallback rule; keyboard 1-5 |
| 6 | Loot/rarity tables | **SKILL** (extend `economy-progression-design`) | `loot-rarity-tables` | weighted roll + `GetPercent` (displayed = real odds); rarity asset (color/frame/fx); luck/mutation tables (TBE); money-band rarity (KT); pity counter |
| 7 | Hit feedback kit | **SKILL** (extend `game-feel-polish`) | `game-feel-polish` + `references/combat-feel.md` | scale punch / rot shake numbers; pooled floating damage text (0.75 s, 1.6 m); HP bar red+yellow trail; shake 0.4/3.5/0.2; FOV punch 12; hit-stop proposal flagged unverified |
| 8 | Throwables and bombs | **RECIPE** | `thrown-bomb-aoe` | pooled arc projectile, inherit velocity, fuse + blink, `OverlapSphereNonAlloc` blast with falloff, owner safety, optional `IDigTerrain` adapter; CT 9-tier table |
| 9 | Terrain dig adapter | **TOOL** | `dig-terrain-adapter` | thin interface over Digger (brush sphere, size x world multiplier, async edit); ground-layer probe; cooldown formula; explicit note that TBE pickaxe is node damage not terrain |
| 10 | Item data anti-patterns | **RULE** | `item-data-driven-behavior` (fold into `config-driven-feature`) | behavior in data class not `switch(Item_Type)`; no `Instantiate` for thrown items; no per-tick allocations; no try/catch around subscribe; cooldown cheats via Factory not inline |

**Top must-haves for the first skill (`tool-weapon-pipeline`):** (1) `Tool_Asset` with `[SerializeReference]` behavior classes and per-tier SO assets; (2) `Tool_User` state machine with impact scheduled at normalized clip time and one `TryUse` entry shared by player/bots; (3) allocation-free target resolver (NonAlloc buffer 32, layer mask, squared range, cone dot, nearest-only mode); (4) `Combat_Health` + `DamageInfo` + `Event_Combat_Hit` that drives floating text/bar/fx/haptic/shake; (5) `Data_Inventory` + static hotbar with reset and slot fallback; (6) tier/price formula DATA file with the x4 ladder and `RoundNice`.
