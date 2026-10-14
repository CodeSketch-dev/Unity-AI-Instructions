# 13 - Roblox -> Unity concept map, genre taxonomy, GDD systems schema

Scope: local single-player Unity clones (SketchEngine) of Roblox hits. Extends, does not duplicate, skills `roblox-genre-patterns`, `roblox-character-camera`, `clone-feature-recipes`, `game-clone-recon`, `gameplay-video-analysis`, `clone-pipeline`, `clone-ip-safety`, `npc-bots-and-enemies`, and catalog files 01/04/05/06.

Evidence tags: **V** = verified (URL or repo file given), **I** = inferred / from engineer knowledge, must be confirmed against the reference video or Studio. "Dev default" = Roblox engine default; many games override it.

Sources fetched this session:
- https://create.roblox.com/docs/workspace/camera (FieldOfView 70, range 1-120; CameraMode Classic / LockFirstPerson) V
- https://create.roblox.com/docs/reference/engine/classes/Humanoid (API page; no defaults listed; MaxSlopeAngle sample only) V
- https://create.roblox.com/docs/reference/engine/classes/Humanoid/JumpPower (StarterPlayer.CharacterJumpPower default 50, range 0-1000) V (via search result summary)
- https://devforum.roblox.com/t/what-exactly-is-jumppower/3029994 (gravity 196.2, JumpPower vs JumpHeight) V (via search summary)
- Repo: `skills/roblox-character-camera/SKILL.md`, `docs/pipeline-catalog/04-gameplay-actors.md` (feel table), `05`, `06`.
- Not confirmed by fetch: WalkSpeed 16 and 1 stud = 0.28 m. Widely quoted (existing skill uses them) -> treat as I; verify in the reference by comparing avatar to doors.

---

## 1. Engine concept -> Unity equivalent

### 1.1 Units, scale, physics

| Roblox | Default | Unity equivalent / formula | Tag |
|---|---|---|---|
| Stud | 1 stud ~ 0.28 m (avatar ~5 studs ~1.4 m R6; R15 ~5.0-5.5 studs) | `const STUD = 0.28f; m = studs*STUD`. Convert at ONE place (`Factory_Units` or static class) | I |
| Many clones scale up | Unity world often 1 stud = 0.5-1 m for readability | Pick world scale per project; keep `speed_m = WalkSpeed*STUD*worldScale`; keep camera/ jump heights proportional | I |
| Humanoid.WalkSpeed | 16 studs/s | 16*0.28 = 4.48 m/s. Stat in `Data`, convert once | I |
| Humanoid.JumpHeight | 7.2 studs (UseJumpPower=false is the modern default) | 7.2*0.28 = 2.0 m | V (search) |
| Humanoid.JumpPower | 50 (0-1000) | `v0 = JumpPower*STUD` = 14 m/s; apex = v0^2/(2g) = 14^2/(2*54.9) = 1.78 m (JumpPower legacy; ~ JumpHeight 7.2 studs = 2.0 m) | V/I |
| Workspace.Gravity | 196.2 studs/s^2 | 196.2*0.28 = 54.9 m/s^2 -> `Physics.gravity = (0,-54.9,0)` (or custom gravity in KCC). Jump from height: `v0 = sqrt(2*g*h)` -> sqrt(2*54.9*2.0)=14.8 m/s | V (devforum) |
| HipHeight | R6 0 (legs form height); R15 ~2.0 studs (varies by rig) | Capsule center offset; Unity capsule `height ~ 1.6-1.8 m`, `center.y = height/2`, skin width 0.08 | I |
| MaxSlopeAngle | 89 deg default, games use 45-55 | KCC `MaxStableSlope`; set 50 for obbies | I |
| AutoJumpEnabled | true on mobile | Usually disable; add jump button instead | I |
| Humanoid.Health / MaxHealth | 100 | `Data` stat, not hardcoded; many games use 1-hit kill zones | I |
| Part (Anchored/CanCollide/CanTouch) | - | Static MeshRenderer+collider; `Anchored=false` -> Rigidbody; `CanCollide=false` -> trigger; `CanTouch` -> registers in `OptCollisionRegister` | I |
| Part sizes | grid 1 stud; typical platform 8x1x8 | 2.24 x 0.28 x 2.24 m; use ProBuilder/primitive scaled cubes (SRP-batch same material) | I |
| Material (Plastic, Neon, SmoothPlastic, Glass, ForceField) | - | Unlit/simple-lit URP material set; Neon = emissive + bloom; Glass = transparent (limit overdraw) | I |
| Terrain (voxel) | 4-stud voxels | Bake to mesh in DCC or use Unity Terrain (low-end: prefer meshes); nothing runtime-voxel | I |
| Workspace gravity / `Workspace.FallenPartsDestroyHeight` | -500 studs | Kill-plane Y = -140 m (500*0.28) or per-level trigger; respawn at checkpoint | I |
| Physics-ownership / network ownership | - | Irrelevant locally; all physics local | I |
| Constraints (HingeConstraint, Spring, AlignPosition) | - | HingeJoint / ConfigurableJoint / DOTween-PrimeTween driven kinematic mover. Prefer kinematic movers (cheap) | I |
| Anchored moving platforms (TweenService on CFrame) | - | `Platform_*` movers in catalog 04 section 7 | V (repo 04) |

### 1.2 Character, rig, camera

| Roblox | Details | Unity equivalent | Tag |
|---|---|---|---|
| R6 rig | 6 parts, 3 anim layers; blocky 1.5x... | One generic Animator + skinned blocky mesh; 6-limb is fine | I |
| R15 rig | 15 parts, scalable body (Height/Width/Head/Proportion scale 0.9-1.05) | Humanoid-ish blockly mesh, 15 bones; body scale -> uniform scale; emotes = Animator states | I |
| Animate script states | Idle, Walk, Run, Jump, Fall, Climb, Swim, Sit, Tool-hold | Animator layers + `StateMachine<CharacterState>` (catalog 04 section 3) | V (repo 04) |
| Humanoid:MoveTo / PathfindingService | - | NavMeshAgent for bots (catalog 04 section 5), waypoint-follow cheapest | V (repo 04) |
| Respawn (Players.RespawnTime ~5 s; CharacterAutoLoads) | - | Respawn at last checkpoint (`Checkpoint`), invuln 1-2 s, optional ad revive | V (repo 04, 05) |
| Ragdoll | BallSocket on death | Reuse skin-detach ragdoll recipe (`roblox-character-camera`) | V |
| Camera defaults | CameraMode Classic, FieldOfView 70 (1-120), MaxZoom 128 / MinZoom 0.5 studs (StarterPlayer) | Cinemachine FreeLook; FOV 70; distance default ~12 studs (3.4 m)... clone often closer 8-12 m; zoom limits = data | V (FOV) / I (zoom 0.5-128) |
| Camera collision (Zoom, Invisicam) | pushes in on obstruction | Cinemachine Collider / spherecast pull-in | I |
| Mobile camera | right-thumb drag orbit, pinch zoom, tap-to-jump button bottom-right | `mobile-input-controls` | V (skill) |
| Mouse lock / Shift Lock | optional | Not needed on touch | I |
| Camera shake / FOV kick | game-defined | `game-feel-polish` | V (skill) |

### 1.3 Interaction and items

| Roblox | Behavior | Unity equivalent | Tag |
|---|---|---|---|
| Touched / TouchEnded | physics overlap, fires for any part | `OptCollisionRegister` + `ICharacterCollidable` (never per-object OnTrigger+GetComponent) | V (CLAUDE.md house style) |
| ProximityPrompt | hold-to-activate (HoldDuration 0-1.5 s), MaxActivationDistance 10 studs (2.8 m), key E / mobile button | `Interactable` registry: trigger zone enables ONE shared "interact" HUD button/ring (hold fill); distance 2.8 m default; one active prompt at a time | I |
| ClickDetector | MaxActivationDistance 32 studs (9 m) | Tap raycast on layer mask, or world-space button | I |
| Tool (StarterPack) | Equipped/Activated/Unequipped, Handle, GripPos; `RequiresHandle` | `Item` config asset + `ItemRuntime` prefab; Equipped -> attach to hand socket; Activated -> action (`Data_Inventory`) | I |
| Backpack / hotbar | 10 slots keys 1-0, tap to equip; Backpack GUI default 10 slots visible | Hotbar 3-6 visible slots on mobile; scroll for more; `Data_Inventory` list of ids+counts | I |
| StarterGear / StarterPack | tools given on spawn | Starting loadout in `Factory_Item` | I |
| Humanoid:EquipTool/UnequipTools | - | `Character.Equip(itemId)` single owner | I |
| leaderstats (Folder in Player with IntValue) | shows top-right leaderboard | HUD currency bar + local leaderboard panel (bots fake) | I |
| Attributes (Instance:SetAttribute) | typed key/value on instances | ScriptableObject fields / `[SerializeField]`; data-driven per prefab variant | I |
| CollectionService tags | group query "Coin", "KillBrick" | Prefab components + registry (`OptCollisionRegister`, `MonoCachedHub` lists); never `FindObjectsOfType` | I |
| BindableEvent / RemoteEvent / RemoteFunction | signals | `StaticBus<TEvent>` locally; RemoteEvent = plain method call | I |
| Debris:AddItem(obj, t) | timed destroy | Pool + `UniTask.Delay` return-to-pool | I |
| TweenService (Linear, Sine, Quad, Back, Bounce; Enum.EasingStyle/Direction) | - | PrimeTween (preferred) with matching Ease: Sine->`Ease.InOutSine`, Back->`OutBack`, Bounce->`OutBounce`, Quad->`InQuad` | I |
| RunService.Heartbeat/Stepped | per-frame | MonoCached tick / UniTask; avoid per-object Update | V (house style) |
| SoundService, SoundGroup, Sound.RollOffMaxDistance (default 10000) | - | Audio mixer groups (BGM/SFX); `game-audio-system`; 3D rolloff distance set small on mobile | I |
| Lighting (Technology, Ambient, ClockTime, Atmosphere, Bloom, ColorCorrection, SunRays, Skybox) | - | URP: ambient color/trilight, 1 directional light, skybox material, Volume Bloom (low intensity, mobile threshold ~1), Color Adjustments; fog = RenderSettings.fog. Match palette from video frame | I |
| Lighting.Technology (Voxel/ShadowMap/Future) | - | mobile: single shadow cascade, 512-1024 shadow map, or bake blob shadows | V (house style) |
| ParticleEmitter / Beam / Trail | - | Particle System (cap particles), TrailRenderer; VFX pooled (`game-feel-polish`) | I |
| Decal / Texture / SurfaceGui | - | Quad with Unlit material / world-space Canvas (batched TMP only if few) | I |
| BillboardGui (nameplates, "x2" over head) | - | World-space TMP billboard via CullingGroup (`world-batching-culling`) | V (skill) |
| Humanoid DisplayName / overhead name | - | nameplate component; bot random names (`npc-bots-and-enemies`) | V |

### 1.4 UI

| Roblox | Unity | Tag |
|---|---|---|
| ScreenGui / Frame / TextLabel / ImageButton | Canvas + panels (`unity-ui`, `ui-clone`) | V |
| UIScale, UIAspectRatioConstraint, UICorner, UIStroke, UIGradient | CanvasScaler (ref 1080x1920 or 1920x1080, match 0.5), 9-slice rounded sprites, TMP outline, gradient sprite | I |
| UIListLayout / UIGridLayout / ScrollingFrame | Layout groups (disable after layout) + ScrollRect (`ui-scroll-board`) | V (house style) |
| TopbarPlus / CoreGui (chat, emote wheel, menu button, leaderboard, backpack) | Reduce to: settings button, currency bar; drop chat | I |
| Emote wheel / chat | Local emote wheel (4-8 animations) if reference uses it socially; chat dropped (use canned bot chat lines at most) | I |
| GuiService.SafeArea / Topbar inset 36 px | Safe area + banner clearance (`mobile-hud-layout`) | V |
| Notification popups, "Rebirth" prompts, offer popups | `ui-pattern-library`, `ads-popup-flow` | V (skills) |

### 1.5 Data, social, monetization

| Roblox | Unity (SketchEngine) | Notes | Tag |
|---|---|---|---|
| DataStoreService / ProfileService | `DataBlock<T>` + `DataValue<T>` local save | No cloud/session lock; add schema version in the data block; backup slot optional | V (house style) |
| MemoryStore / OrderedDataStore (global leaderboard) | Fake leaderboard Data (see section 5) | | I |
| MarketplaceService gamepass | `IAP` non-consumable (multiplier, VIP, auto-collect, extra slots) | `unity-iap-port`, catalog 05 | V (repo) |
| Developer product | IAP consumable (coins pack, instant hatch, revive) | | V |
| Premium benefits / Premium payouts | Skip; replace by "VIP subscription" if reference shows it (catalog 05 `Subscription_VIP`) | | V (repo 05) |
| Robux price (e.g. 99, 199, 399, 799, 1599 R$) | Map to store tiers ($0.99/$1.99/$2.99/$4.99/$9.99 ... ) by ratio; Robux ~ $0.0125/R$ to dev ... pick tier by rank, not by math | I |
| Badges | Local achievements list (`Data_Achievements`) | | I |
| Rebirths | Prestige loop recipe 8 | V (skill) |
| Friends / Party / private servers / VIP server | Remove; "Invite friends" -> share sheet reward (optional); party boost -> fake `+X% with N friends online` | I |
| TeleportService (between places) | Scene load / additive scene (world 1 -> world 2; lobby -> minigame), see 06 | V (repo 06) |
| Player join/leave toasts, server size (e.g. 10-30 players) | Bots population 8-30 (cap by perf) | I |
| Group-only content / UGC accessories | Fixed cosmetic catalog (`clone-ip-safety`) | V |
| DevProducts "skip stage" | Rewarded ad skip | I |
| Daily rewards, Spin wheel, Time rewards (play-time gifts 1/5/10/20 min) | recipe 9, `Jackpot`, `Data_TimeReward` | V/I |
| Server events (e.g. "Admin abuse", "x2 luck event") | Local timed events by device clock (offline events) | I |

---

## 2. Top-25 mobile-friendly genres / sub-genres

Coverage legend: **S** = covered by existing skill/recipe, **P** = partial, **M** = missing (new skill proposed, see section 6). Numbers are typical (I), study the reference's numbers.

| # | Genre | Core loop | Required systems | Typical numbers | Monetization hooks | Coverage |
|---|---|---|---|---|---|---|
| 1 | Obby (obstacle course) | Run/jump stages -> checkpoint -> finish -> next | Character, camera, checkpoints, hazards, movers, stage counter, kill plane | 50-500 stages; checkpoint every stage; 1-3 min per 10 stages | Skip stage (R$), rewarded revive, trail/gear shop, VIP | S (genres Obby, recipe 4/5, catalog 04) |
| 2 | Tower climb ("Tower of Hell", "Escape ... Tower") | Climb vertical course without checkpoints, timed rounds | Section generator (random sections), timer, win zone, gravity coil/tools | 8-15 sections, 5-8 min round | Gear (coil, jump), cosmetics, revive | P (need `zone-level-design`+random sections recipe M) |
| 3 | Simulator (collect/sell/upgrade) | Click/collect -> backpack fills -> sell -> buy upgrade -> new zone | Currency, backpack capacity, sell pad, tool upgrade, zones/gates, pets, rebirth | Zone gate costs x5-x10 per zone; backpack 10 -> 10,000; rebirth at 1M-1B | 2x coins, 2x luck, auto-collect pass, pet slots, x2 speed | S (genres Simulator, recipes 4,7,8) |
| 4 | Pet collecting / hatching | Buy egg -> hatch -> equip best -> boost -> next egg | Egg shop, rarity table, hatch anim, pet inventory, equip slots, merge/evolve, index | Rarity 60/25/10/4/0.9/0.1 %; equip 3-6, upgrade slots 3->10 | Lucky/Super lucky gamepass, auto hatch, 3x hatch, exclusive pets | S (recipes 1,2,10), P evolve/merge M |
| 5 | Tycoon (classic) | Buy droppers/conveyors -> money -> buy next pad | Plot, buy pads (button part, price tag), droppers, collectors, upgrades, rebirth | Pad cost x1.5-2 per step; 30-100 pads | 2x cash, auto-collect, premium dropper, VIP | M (`tycoon-plot` skill) |
| 6 | Tycoon-lite / idle base | Few stations produce idle income; offline earnings | Stations, workers/NPC, income per second, offline | income/s doubling every 2-3 upgrades | Speed x2, offline x2 rewarded | P (recipe 15, 2) |
| 7 | Steal-a-brainrot / carry-and-defend | Hatch/collect creatures -> base income -> others steal | Spawn belt conveyor of creatures, buy, carry, base slots, lock timer, steal AI (bots), lasers/bat | Belt every 5-10 s; rarity tiers Common..Secret; lock 60 s; income $/s per creature | Lock, speed coil, luck, instant brainrot, VIP | S (genres Steal/carry, recipe 2, bots 12) |
| 8 | Escape / hide (flee a chaser) | Run from killer to exit, collect keys | Chaser AI, safe zone, keys/pickups, hide spots, win door, scoring | Chaser speed 0.8-1.1x player; round 3-5 min | Revive, speed boosts, skins | S (recipe 5, `npc-bots-and-enemies`) |
| 9 | Survive-X (survive the disaster, kill brick, flood) | Timed round with random disaster, last alive wins | Round state machine, disaster set (flood, meteor, fire), spectator, map select, bots | 30-120 s rounds; 6-20 players | Revive, cosmetics, double reward | P (`06` game-flow; `round-minigame` skill M) |
| 10 | Horror escape (Doors, Piggy, Rainbow Friends) | Room-by-room explore, avoid entity, keys/puzzles | Rooms generator (random), entity events (light flicker, rush), hiding closet, items, death/revive | 100 doors; entity every 30-90 s | Revive tokens, flashlight, cosmetics | P (needs `room-run` M; horror in genres) |
| 11 | Speed/treadmill/idle run | Run on treadmill, speed = currency; race ladder | Treadmill zones, speed stat, speed->worlds, pets | Speed *1.1-1.5 per upgrade | Speed x2, pets | S (genres Treadmill, recipe 3) |
| 12 | Battle / arena (sword/gun fight) | Spawn -> loot/kill -> level | Combat, weapons, hit detection, health, respawn, killstreak, bots | HP 100, sword dmg 10-30, cooldown 0.6 s | Weapons, crates, VIP | P (`combat-melee-ranged` M) |
| 13 | Tower defense | Waves, place units, upgrade | Grid/path, units, waves, targeting, upgrades, gacha | 40-60 waves; unit cost 100-5k | Units gacha, speed x2/x3, passes | P (genres TD; skill `tower-defense` M) |
| 14 | Racing / bike / car | Race track vs bots, upgrades | Vehicle physics (arcade), track, checkpoints, rubber-band bots, garage | 3 laps; 3-6 racers | Cars, boost, VIP | M (`vehicle-arcade` skill) |
| 15 | Parkour / wall-run (Parkour, "Flee") | Run on obstacles with extra moves | Movement abilities (wall-run, slide, double jump, grapple), courses, timer | 5-10 moves; ghost/best time | Gear, trails | P (character skill; `movement-abilities` M) |
| 16 | Dress / avatar / roleplay (Dress to Impress, Brookhaven-lite) | Choose outfit -> catwalk -> vote/score | Wardrobe, item catalog, theme, scoring (bots as judges), photo mode | 3-10 themes, 1-2 min round | Outfit packs, VIP, emotes | M (`wardrobe-fashion` skill) |
| 17 | Idle clicker | Tap -> coins -> auto -> prestige | Click, upgrades, auto-clicker, prestige, offline | cost ^1.07-1.15 per level | x2, auto, offline | S (economy skill, recipe 7,8,15) |
| 18 | Mining / digging | Dig blocks -> ores -> sell -> better pickaxe -> deeper layer | Voxel/block grid dig, ore table per depth, pickaxe stats, backpack, layers | depth 1000+ layers; ore rarity per layer | Pickaxe, backpack, auto-mine | M (`dig-mine` skill; chunked grid) |
| 19 | Fishing | Cast -> wait -> minigame -> fish -> sell | Rod, bait, fish table, timing minigame, sell, zones | bite 3-8 s; rarity tiers | Rod, luck, auto-fish | M (`fishing-minigame` recipe) |
| 20 | Cooking / restaurant | Take order -> cook -> serve | Stations, recipes, customers AI, tips, upgrades | customer every 10-20 s | Upgrades, speed | M (`service-loop` recipe) |
| 21 | Farming (Grow a Garden style) | Plant -> wait timer -> harvest -> sell | Plots, seeds, growth timers (real-time), mutations, weather events, pets | grow 10 s - 30 min; mutations 1-5% | Seeds, instant grow, VIP | M (`farm-timer` recipe; uses offline time) |
| 22 | Block-building / creative sandbox | Place blocks, share | Grid placement, palette, save slots, undo | 1-4k blocks cap | Block packs | M (rare local; `build-sandbox` skill, low priority) |
| 23 | Minigame hub / party (Mini games, "Wacky Wizards"?) | Lobby -> random minigame -> reward | Lobby, queue, 5-15 minigames, round rewards, bots | 1-3 min per game | Cosmetics, boosters | S (`06` minigames, flow) |
| 24 | Fight-the-boss / raid / "Boss Rush" | Co-op vs boss | Boss state machine, phases, party bots | boss HP 10^5+ | Weapons | P (recipe 5; `boss-fight` M) |
| 25 | Trading card / collection ("Anime ...", "Sol's RNG" roll) | Roll RNG -> collect rare -> index | Roll button, rarity table w/ luck, aura/VFX, index, auto-roll | rarities 1/2 to 1/1M; roll cooldown 0.5-2 s | Luck potions, auto-roll, faster roll | P (recipe 1,10; `roll-rng` recipe M) |

---

## 3. Systems checklist (what a GDD must capture) - YAML schema

This is the machine-readable outline the GDD generator fills. Every key is mandatory unless `n/a`; each leaf carries `value`, `source` (video timestamp / screenshot / wiki URL) and `confidence` (VERIFIED/INFERRED). Reuse `game-clone-recon` fidelity labels.

```yaml
meta:
  title: ""
  roblox_url: ""            # place id / game URL (for human only; never copied assets)
  genre: [simulator, pet]   # keys from section 2 (primary first)
  platform_target: android-lowend
  fidelity: {gameplay: exact, ui: close, art: original, audio: original}   # clone-ip-safety
  session_length_s: 180
  first_reward_s: 30

scale:
  stud_m: 0.28
  world_scale: 1.0
  avatar_height_studs: 5
  gravity_studs: 196.2

movement:
  walk_speed: 16            # studs/s, progression-driven? true/false
  speed_source: stat|treadmill|item|pet|rebirth
  jump: {mode: height|power, value: 7.2, double_jump: false, coyote_s: 0.1}
  abilities: [sprint, slide, wallrun, swim, climb, fly, glide, vehicle]
  respawn: {mode: checkpoint|spawn|instant, invuln_s: 1.5, kill_y: -500}
  states: [idle, run, jump, fall, carry, action, ragdoll, sit]
  rig: R6|R15|custom
  skins: []

camera:
  mode: third_person|top_down|first_person|fixed_side
  distance: {min: 0.5, default: 12, max: 128}   # studs
  fov: 70
  pitch: {min: -10, max: 80}
  collision: true
  special: [shake, fov_kick, cutscene_on_hatch]

input:
  touch: {move: joystick|tap_to_move|none, look: right_drag, buttons: [jump, interact, sprint, action, hotbar]}
  auto: [auto_collect, auto_attack, auto_hatch, auto_roll, auto_run]
  prompts: {proximity_distance_studs: 10, hold_s: 0}

interaction:
  prompts: [{id: sell_pad, type: touch|prompt|click|tool, range_studs: 10, hold_s: 0, effect: ""}]
  tools: [{id: "", activation: click|hold, cooldown_s: 0.5, effect: ""}]
  hazards: [{id: lava, effect: kill|knockback|slow|damage, amount: 0}]

economy:
  currencies: [{id: coins, source: [], sink: [], cap: null, display: abbreviated}]   # K M B T Qa
  formulas: {upgrade_cost: "base*growth^level", income: "base*mult", rebirth_mult: ""}
  multipliers: [{id: gamepass_2x, stack: multiplicative|additive}]
  offline: {enabled: true, cap_h: 8, rate: 0.25}

progression:
  zones: [{id: z1, gate: {stat: speed, value: 100}, recommended: "", theme: ""}]
  levels_xp: {}
  rebirth: {requirement: 1e6, reward: "x1.5 per rebirth", resets: [coins, upgrades], keeps: [pets, passes]}
  unlock_chain: []          # dependency order of systems/features
  achievements: []          # badges
  milestones: []

shops:
  - {id: egg_shop, kind: egg|gear|trail|boost|skin|currency|gamepass|offer, items: [], currency: coins, rotation: static|timed}
inventory:
  type: hotbar|backpack|capacity_stat|pet_slots
  limits: {slots: 10, stack: 99, backpack_capacity: 10}
  equip_rules: ""
quests:
  daily: []
  timed_rewards: [60, 300, 600, 1200]    # s
  tutorial_quests: []
  streak: {days: 7, rewards: []}

pets:
  rarity_table: [{tier: common, chance: 0.6, mult: 1.0}]
  hatch: {anim_s: 2.5, skip: true, auto: true, multi: [1, 3, 8]}
  equip_slots: 3
  evolve: {merge_n: 5, golden: true, rainbow: true}
  abilities: [boost, collect, fight, fly]
  follow: {offset: [], style: orbit|line}

combat:
  mode: none|melee|ranged|collision|ability
  stats: {hp: 100, dmg: 10, cooldown_s: 0.6, range_studs: 5}
  enemies: [{id: "", hp: 0, speed: 0, ai: chase|patrol|stationary|boss_phases}]
  loot: []

npc_bots:
  as_players: {count: [8, 24], tiers: [weak, normal, vip], names: random, join_leave: true}
  behaviors: [wander, collect, steal, chase, race, build]
  population_cap: 24
  fake_chat: []

level:
  structure: hub|linear|zones|rounds|procedural|plot
  zones: []
  checkpoints: {every: 1}
  movers: [rotating, sliding, falling, conveyor, teleporter, trampoline, ladder, laser]
  segments_random: false
  bounds: {size_m: [], max_draw_calls: 150}

ui_screens:
  hud: [currency, stats, minimap, quest_tracker, buttons]
  popups: [shop, offer, rebirth, reward, index, settings, pass, daily, spin, revive, result]
  flows: [boot, home, play, result, reward]
  notifications: [toast, rare_drop_banner, join_leave]
  safe_area: true

audio: {bgm: [], sfx: [], ui_clicks: true, ducking: false, rolloff: short}
vfx: {hit: [], collect: [], hatch: [], rebirth: [], trails: [], aura: [], screen: [bloom, flash]}
lighting: {time_of_day: "", ambient: "", fog: "", skybox: "", bloom: 0.3, shadow: blob|single}

monetization:
  iap: [{id: "", type: consumable|nonconsumable|subscription, effect: "", price_tier: 1.99}]
  ads: {rewarded: [{id: "", reward: ""}], interstitial: {gate_s: 90, placements: []}, banner: true}
  vip: {price: "", perks: []}
  offers: [{id: starter_pack, trigger: first_session, expires_s: 3600}]

retention:
  daily_login: {days: 7}
  spin_wheel: {cooldown_h: 4}
  timed_events: []          # local clock
  notifications: [{id: "", delay_h: 24}]
  collection_index: true
  leaderboards: [{id: "", fake: true}]

tutorial: {steps: [{id: "", trigger: "", arrow: true, lock_input: false}], skip: false}
localization: {languages: [en], rtl: false, text_inventory: file}
meta_systems: [settings, privacy_consent, rate_us, save_backup, cheats_debug]
local_substitutes: []        # mapping from section 5
unknowns: []                 # open questions for human
```

Checklist rules:
1. Every enumerated list (zones, eggs, pets, tools, products) needs a COUNT before building (number of items, not just names).
2. Any value with `confidence: INFERRED` goes into `unknowns` for verification.
3. Gameplay-video-analysis fills `movement, camera, interaction, level`; wiki/community sources fill `economy, pets, shops`; store listing fills `monetization`.
4. Ordering: `unlock_chain` decides build order (vertical slice first: movement -> core loop -> first shop -> first zone).

---

## 4. Genre -> systems matrix (what to scan the GDD for)

| System | obby | tower | sim | pet | tycoon | steal | escape | survive | horror | tread | arena | TD | racing | parkour | dress | idle | mine | fish | cook | farm | roll |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Character+camera | x | x | x | x | x | x | x | x | x | x | x | - | x | x | x | - | x | x | x | x | - |
| Checkpoints/stages | x | x | - | - | - | - | - | - | rooms | - | - | waves | laps | x | - | - | - | - | - | - | - |
| Currency/economy | opt | opt | x | x | x | x | opt | opt | opt | x | x | x | x | opt | x | x | x | x | x | x | x |
| Upgrades | - | - | x | x | x | x | - | - | - | x | x | x | x | - | - | x | x | x | x | x | x |
| Zones/gates | - | - | x | x | - | - | - | - | - | x | - | - | - | - | - | - | layers | x | - | - | - |
| Pets | - | - | x | x | - | x | - | - | - | x | - | - | - | - | - | - | opt | opt | - | x | opt |
| Bots as players | x | x | x | x | - | x | x | x | x | x | x | - | x | x | x | - | - | - | - | - | - |
| Combat/AI enemies | - | - | - | - | - | x | x | x | x | - | x | x | - | - | - | - | - | - | - | - | - |
| Rebirth | - | - | x | x | x | x | - | - | - | x | - | - | - | - | - | x | x | x | - | x | x |
| Timers/offline | - | - | - | opt | x | x | - | - | - | - | - | - | - | - | - | x | - | - | - | x | - |

(x required, opt optional, - not used) - I (engineer judgement).

---

## 5. What cannot be cloned locally and standard substitutes

| Roblox feature | Why not | Local substitute | Tag |
|---|---|---|---|
| Server authority / anti-cheat | No server; player owns device | Accept local cheats; obfuscate nothing; disable only IAP-affecting exploits via store receipts | I |
| Real multiplayer (other players on the map) | No netcode | Bots driven by same character systems (`npc-bots-and-enemies`), 8-24, tiered, random names, join/leave | V (skill) |
| Real-time stealing/PvP between players | Needs players | Bot "thieves" with schedule/aggro; player defends or locks base; losses capped + rewarded-ad restore | I |
| Global leaderboards | No backend | Fake leaderboard: generate N entries seeded per device, scores = player_score * rank-curve; bots overtaken/dropped as player progresses; refreshed on session start; weekly reset by device clock | I |
| Trading, auctions, global economy | Requires players | Remove, or NPC trader with fixed exchange rate | I |
| Chat / social | UGC & moderation | Remove; optional canned bot chat | I |
| Friends/party/private server | Requires accounts | Remove; "invite" -> share sheet bonus | I |
| Server-wide events ("event in 5 min for all players") | No shared clock | Local timed events on device time (UTC) with anti-clock-cheat grace: store last-seen time; allow rewarded skip | I |
| Admin events/server hops | - | Scripted random event timer (e.g. "meteor shower" every 8-15 min) | I |
| UGC (player-built plots, custom maps, accessories, avatar items) | Cannot import real avatar catalog | Fixed cosmetic catalog; plot customization from palette only; no `HumanoidDescription` | V (`clone-ip-safety`) |
| Player avatar (Roblox account) | No account | Default blocky avatar + skin shop | I |
| Server persistence (DataStore, cross-device) | Local only | `DataBlock` local save; optional cloud save later (out of scope) | V (house style) |
| Premium / Robux payments | Store | IAP with store tiers; Robux -> consumable mapping | I |
| Server-side random seeds (shared world seed) | - | Local seed; per-session random | I |
| Chat commands / admin panels | - | `debug-cheats-menu` | V (skill) |
| Real-time global announcements ("X hatched a SECRET") | - | Fake announcements from bot names with probability tied to rarity | I |
| Large persistent worlds (>100 players visible) | Perf | Cap bots, cull, `world-batching-culling` | V (skill) |

---

## 6. Gaps -> proposed classification

Existing coverage (V): genres 1, 3, 4, 7, 8, 11, 17, 23 well covered; 2, 6, 9, 10, 12, 13, 15, 24, 25 partial; 5, 14, 16, 18-22 missing.

### Proposed classification

**RULE (always-on, short)**
- `rule-roblox-units`: single `STUD=0.28` conversion point; WalkSpeed/Jump/gravity table in section 1.1; never put studs in gameplay code. Must-haves: (1) one conversion class, (2) jump via `v0=sqrt(2gh)` with g=54.9, (3) stats in Data, (4) verify scale against doors in reference frame, (5) mark world_scale in GDD, (6) kill-plane/respawn standard.
- `rule-local-substitutes`: section 5 table as policy. Must-haves: (1) no netcode, (2) bots via real character, (3) fake leaderboard recipe, (4) local timed events, (5) no UGC/avatar import, (6) no server-authority claims.

**SKILL (new)**
- `roblox-to-unity-map`: this document's section 1 as a lookup skill (Touched, ProximityPrompt, Tool, leaderstats, Attributes, CollectionService, Tween, DataStore, gamepass). Must-haves: (1) concept->SketchEngine table, (2) interaction prompt component spec, (3) tag/attribute replacement rules, (4) tween easing map, (5) lighting/bloom look preset, (6) UIScale equivalents.
- `gdd-systems-schema`: the YAML in section 3 + filling workflow. Must-haves: (1) schema file, (2) per-key source/confidence, (3) unknowns list, (4) build-order via unlock_chain, (5) count-everything rule, (6) link to game-clone-recon fidelity.
- `tycoon-plot`: plot/pad/dropper/conveyor/collector loop. Must-haves: (1) buy-pad price tag + unlock order, (2) dropper/conveyor pooling, (3) collector income math, (4) save plot state in Data, (5) rebirth reset, (6) cost curve.
- `movement-abilities`: sprint/slide/wall-run/double-jump/glide/grapple/climb/vehicle-lite on top of the KCC controller. Must-haves: (1) ability as state, (2) stamina stat, (3) touch buttons, (4) animation hooks, (5) kill/respawn compat, (6) tuning table.
- `combat-melee-ranged`: sword/gun/ability, health, hit detection, bot targeting. Must-haves: (1) hit detection via collision registry/NonAlloc, (2) cooldown/damage in config, (3) auto-attack for mobile, (4) death/respawn, (5) damage numbers pooled, (6) bots use same API.
- `dig-mine-grid`: chunked grid digging with ore tables per depth. Must-haves: (1) cell grid + chunk mesh, (2) ore table by layer, (3) pickaxe stats, (4) backpack capacity, (5) pooling/culling, (6) save only modified cells.
- `vehicle-arcade`: car/bike for racing. Must-haves: (1) kinematic/arcade physics, (2) checkpoints/laps, (3) rubber-band bots, (4) garage upgrades, (5) camera follow, (6) drift/boost.

**RECIPE (add to clone-feature-recipes)**
- `roll-rng` (RNG roll with luck, aura, index), `fishing-minigame` (cast/bite/timing), `farm-timer` (plots, real-time growth, mutations, offline), `service-loop` (cooking/restaurant customers), `round-minigame` (lobby->round->result for survive-X/disaster), `random-section-course` (tower climb/doors procedural sections), `pet-merge-evolve`, `belt-conveyor-steal`, `fake-leaderboard`, `local-timed-events`, `interactable-prompt` (ProximityPrompt equivalent). Must-haves per recipe: data+config+factory chain, edge cases (offline/clock), test scenarios, perf note.

**TOOL**
- `roblox-wiki-scraper` (read-only fetch of fandom/wiki tables -> CSV for pets/items/rates; respect ToS, no asset copy). Must-haves: (1) CSV output, (2) source URL per row, (3) rarity/stat normalizer, (4) human review flag, (5) clone-ip-safety guard, (6) cache.
- `gdd-lint`: validates YAML vs schema (missing keys, counts, INFERRED leaks). Must-haves: (1) key presence, (2) numeric ranges, (3) list counts, (4) unlock_chain cycle check, (5) export unknowns, (6) JSON schema.
- `unit-converter` Editor tool: paste studs -> meters on selected prefabs/colliders; validate avatar vs door ratio.
- `fake-leaderboard-gen`: seeded generator + curve fit.
- `place-importer-notes` NOT proposed (copying Roblox place geometry violates `clone-ip-safety`).

**DATA**
- `data/roblox-defaults.yaml`: all numeric defaults of section 1 with V/I tags. Must-haves: (1) stud constant, (2) humanoid defaults, (3) camera, (4) prompt distances, (5) gravity/jump formulas, (6) legacy vs current flags.
- `data/genre-templates/*.yaml`: pre-filled GDD schema per genre (25 files) with typical numbers from section 2. Must-haves: (1) required systems, (2) typical numbers, (3) monetization hooks, (4) recipe links, (5) risks, (6) vertical-slice order.
- `data/rarity-tiers.yaml` (Common 60, Uncommon 25, Rare 10, Epic 4, Legendary 0.9, Mythic 0.1; luck multiplier function), `data/price-tier-map.yaml` (R$ -> store tier), `data/fake-names.txt` (bot names, original, not real accounts).

### Verification backlog (INFERRED -> confirm)
1. 1 stud = 0.28 m (find Roblox docs statement). 2. WalkSpeed default 16. 3. Camera zoom 0.5-128. 4. ProximityPrompt MaxActivationDistance 10 and ClickDetector 32. 5. R15 HipHeight ~2.0. 6. MaxSlopeAngle default 89 (docs sample shows 30 is only a sample). Use https://create.roblox.com/docs/reference/engine/classes/Humanoid.md and StarterPlayer/ProximityPrompt/ClickDetector API pages.
