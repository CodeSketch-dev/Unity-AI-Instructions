# 04 - Core Gameplay Actors (reverse-engineering catalog)

Scope: Character, Player, Camera, Input, AI, Navigation, Boss, Pet, Wing, Aura, Trail, Platform, Ladder, Checkpoint, Teleporter, Trigger, Interactive, Obstacle, Tower, Treadmill.
Projects (read-only): **KT** = `knife-tower/knife-tower-troll-unity`, **ME** = `monkey-escape/monkey-escape-unity`.
Path shorthand: `L/` = `Assets/_Game/Scripts/Logic/`, `CFG/` = `Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/`, `KC/` = `L/Character/KinematicController (KC)/`.
Tags: **[V]** verified in cited file/asset, **[I]** inferred. Both projects use the CodeSketch framework (`OptCollisionSensorFast`, `OptCollisionRegister<T>`, `StaticBus`, `StateMachine<T>`, `DataValue<T>`), Cinemachine 2.10.7 FreeLook, KinematicCharacterController (KCC) asset, PrimeTween + DOTween, UniTask, Odin [V: both `Packages/manifest.json`, `CharacterKC.cs` usings].

---------------------------------------------------------------------------
## 1. Architecture at a glance

| Layer | KT | ME | Notes |
|---|---|---|---|
| Actor root | `Character : OptCollisionSensorFast<ICharacterCollidable>` (985 lines) `L/Character/Character.cs` [V] | same base, 455 lines `L/Character/Character.cs` [V] | ME is the trimmed fork: no attack/ragdoll/effect/item/FNAF/squid partials [V file lists] |
| Motion | `CharacterKC : MonoBase, ICharacterController` (KCC), 2068 lines `KC/CharacterKC.cs` [V] | 2996 lines + `CharacterKC.Swing(.API).cs` (rope swing, 923 lines) + `CharacterKC_Sink.cs` [V] | ME adds WallJump, Swing, Sink states to the same controller |
| Tuning | `Factory_CharacterKC` (ScriptableObjectSingleton, static getters) [V `KC/Factory_CharacterKC.cs`] | `Factory_CharacterKC` holds `_default` -> `CharacterKC_Asset` SO; per-minigame override asset `CharacterKC._overrideConfig` [V `KC/CharacterKC_Asset.cs`, `CFG/Game.Factory_CharacterKC.asset`] | ME evolved tuning into swappable SO profiles (Escape vs Obby) because it has 2+ minigames with different feel [I] |
| Components | `Character_Component : MonoCached` siblings: Renderer, Animator, Checkpoint, Dead, Sfx, Fx, FallDetector, Skin, Wing, Item, Effect, Attack, Ragdoll, UI, Scale [V] | Renderer, Animator, Checkpoint(+_Escape/_Obby), Dead, Sfx, Fx, FallDetector, Skin, Monkey, Treadmill, Tail, Carpet [V] | composition: root holds `[SerializeField]` refs, exposes read-only props |
| Driver | `Player : MonoSingleton<Player>` + `PlayerControl` + `PlayerGUI` / `AI : MonoCachedFast` -> both write a `CharacterKCInputPlayer` / `CharacterKCInputAI` struct into `CharacterKC.SetInputs(ref input)` [V `Player/PlayerControl.cs`, `AI/AI.cs`] | same | "same character, different driver" |
| World contact | Platforms/pickups/zones derive `OptCollisionRegister<ICharacterCollidable>`; Character forwards physics callbacks [V `Character/ICharacterCollidable.cs`, `Platform/*.cs`] | same | `Character_Skin_Switcher`, `Checkpoint`, `Teleporter`, `Trigger_*` all share this |
| Cross-system events | `StaticBus<Event_*>` (e.g. `Event_Checkpoint_Enter`, `Event_Trampoline_Bounced`, `Event_Camera_Reset`, `Event_Wing_Equip`) [V] | same | C# `event Action` for tight owner (`Character.EventDead/EventRevive/EventTick`) |

`ICharacterCollidable` = 4 callbacks (`OnCollisionEnter/Exit`, `OnTriggerEnter/Exit` taking `Character`) [V `Character/ICharacterCollidable.cs`]. `Character.EventTick/EventFixedTick` are re-broadcast Update/FixedUpdate so child components subscribe instead of owning their own Update [V `Character.cs` L~95-110].

---------------------------------------------------------------------------
## 2. The FEEL TABLE (numbers a Roblox clone needs)

### 2.1 Locomotion (CharacterKC, both projects)

| Parameter | KT value | ME Escape | ME Obby | Where | Evidence |
|---|---|---|---|---|---|
| Walk/run max speed (stable) | **4.5 m/s** | 4.5 (+levels) | **6.75** (=4.5x1.5) | KT: `CFG/Game.Factory_CharacterKC.asset`; ME: `Configs/Character/Kinematic/CharacterKC_MonkeyEscape.asset`, `..._MonkeyObby.asset` | [V] |
| Ground accel ("sharpness") | 1000 (exp lerp => instant) | 1000 | 1000 | same | [V] `Mathf.Lerp(v, target, 1-exp(-1000*dt))` KC L1087 |
| Air max speed | 4.5 | 4.5 | 6.75 | same | [V] |
| Air accel | 1000 (effectively instant air control) | 1000 | 1000 | same | [V] |
| Air drag | 0.1 (`v *= 1/(1+drag*dt)`) | 0.1 | 0.1 | same | [V] |
| Gravity | **-30 m/s^2** (Physics.gravity left at -9.81, KC uses its own vector) | -30 | -30 | `_gravity` in SO; setter `Factory_CharacterKC.SetGravity` | [V] |
| Jump up speed | **11 m/s** | 11 | **16.5** | same | [V] |
| **Jump height (derived)** v^2/2g | **2.02 m** | 2.02 m | **4.54 m** | computed | [V math from values] |
| Air time (derived) 2v/g | 0.73 s | 0.73 s | 1.1 s | computed | [V math] |
| Jump pre-ground grace (input buffer) | 0.5 s | 0.5 | 0.5 | `_jumpPreGroundingGraceTime` | [V] |
| Jump post-ground grace (coyote) | 0.5 s | 0.5 | 0.5 | `_jumpPostGroundingGraceTime` | [V] (unusually long vs usual 0.1) |
| Max jumps | 1 (`_maxJumpCount`, `SetMaxJumpStep(2)` for double jump; NPC air-jump x1.5) | same | same | code field | [V KC L~118, L1190-1215] |
| Ladder climb speed | 5 m/s | 5 (+speed add) | 7.5 | same | [V] |
| Ladder enter/exit lerp | 100 (KT, ME) (code default 15) | 100 | 100 | `_ladderEnterSpeed/_ladderExitSpeed` | [V assets] |
| Orientation | `TowardsMovement`; slerp factor hard-coded `1-exp(-100 dt)` (so instant turn); `_orientationSharpness=10` only gates >0 | same | same | KC L875-935 | [V] - the 10 is dead tuning; copy the 100 |
| Hero landing | fall >= **25 m** => Freeze **0.6 s** + hero-landing anim/sfx (code default 10 / 0.75) | 25 / 0.6 | 25 / 0.6 | SO | [V] |
| Capsule | r 0.3, h 1.7, yOffset 0.85 | same | same | SO + `Character.prefab` KCC motor | [V] |
| KCC motor | MaxStepHeight 0.5, **MaxStableSlopeAngle 60**, LedgeDenivelation on, MaxStableDistanceFromLedge 0.3, StepHandling 1, MaxMovementIterations 5, `InteractiveRigidbodyHandling` 1 | same but **MaxStableSlopeAngle 89** | same | `Prefabs/Character/Character.prefab` | [V] ME climbs near-vertical obby slopes [I] |
| Fall kill threshold | `CharacterFallDetector._threshold` **20 m** below last stable ground (NPC forced 5) | 20 | 20 | prefab + `CharacterFallDetector.cs` | [V] |
| Respawn delay | 2.0 s (`Factory_Character._reviveDelay`) | 2.0 | 2.0 | `CFG/Game.Factory_Character.asset` | [V] |
| Jump booster | `BoosterJumpMultiple` 1.7 (vertical multiplier on `_jumpUpSpeed`); wing `_jumpMutiplier` 2 (additive on multiplier); coil `FallDecreaseRate` lowers fall gravity | - | - | `Character.cs` L910, `Character_Wing.cs`, `Character_Item.cs` | [V] |
| Jetpack | power 30, duration 3 s, refuel 1 s, jumpMagnitude 0.3 | same (unused) | | SO | [V] |
| Fly carpet | speed 8, accel 8, yaw 120 deg/s, extra x1.25, camera FOV 60, rig x1.25 | same | | SO / `CameraThirdPerson` | [V] |
| Ladder probe | BoxCast 0.2 cube, 0.35 up, reach `radius+0.1`, every 0.05 s, only with move input | same | | KC L978-1010 | [V] |
| Anti-pop guard | `_maxNoJumpUpwardSpeed` 1.5 m/s when enabled | | | KC fields | [V] opt-in (`LimitNoJumpUpwardPop`) |

Roblox comparison [I, uses repo skill `roblox-character-camera`]: Roblox WalkSpeed 16 studs = ~4.5 m/s - **KT/ME Escape base 4.5 matches exactly**; Roblox gravity ~55 m/s^2 vs **30 used here** (floatier but with tall 11 m/s jump => 2.0 m = Roblox JumpHeight 7.2 studs). So the recipe is: keep speed 4.5, pick jump height 2 m, use g=30 => v=sqrt(2*30*2)=11.

### 2.2 ME progression-driven speed (not in KT)
- Real speed = `Factory.StableMoveSpeedMax (4.5) + speedAdd`, `speedAdd = max(0, level - world.LevelRequired) * _characterSpeedAdditivePerLevel` (**0.5/level**, World_1..3) [V `Character_Monkey.ApplyActualSpeed`, `Configs/Monkey Escape/World/World_1.asset`].
- Jump bonus **+0.1 m/s per level**, same gate [V same files]. Display speed -> real: `(display + 14.5) / 5` [V `Factory_MonkeyEscape.DisplaySpeedToReal`].
- `SpeedLimitFactor` (0..1) scales the *added* speed: `StableMoveSpeedMax = base + add * factor` [V KC L39-43]. Used for the speed slider (`Player_SpeedSliderFeedback`).
- XP tick: `SpeedEarnInMovingEverySeconds = SpeedEarnInTreadmillEverySeconds = 0.15 s` [V `Game.Factory_MonkeyEscape.asset`]; required moving speed >0.5 m/s [V `Character_Monkey.Update`].
- Air steering penalty by angle: 0 deg=100%, 90=50%, 180=0% (`AirSteeringSpeedPoints`) [V KC L184].
- High-speed FOV: boost = `MaxSpeedFOV - DefaultFOV` (default 60-50=+10 deg), starts at `speed01 >= 0.95`, rise over `ExtraSpeedRampDuration` 1 s, release 0.35 s; speed-lines FX at 0.7 [V KC `UpdateHighSpeedFOV`, `HighSpeedFxThreshold`].

### 2.3 Camera (Cinemachine FreeLook, `Prefabs/Player/Player_Camera.prefab`)

| Parameter | KT | ME | Evidence |
|---|---|---|---|
| Rig type | CinemachineFreeLook, 3 orbits, **all damping 0** (X/Y/Z damping 0, composer damping 0, lookahead 0, dead zone 0, soft zone 0.8) | identical | [V prefab] |
| Orbits (height, radius) | Top (6, 1) / Mid (3, 6) / Bottom (-1, 3) then **Bottom overridden at runtime to (-5, 1)** via `Factory_Camera._bottomRigNormal`; carpet (-5, 3) | identical | [V prefab, `Factory_Camera.cs`, `Player.cs` L267] |
| Mid-rig distance | sqrt(3^2+6^2) = **6.7 m** behind, 3 m up; follow offset (0,3,-6) | same | [V prefab m_FollowOffset] |
| Follow pivot offset | `_followOffset` (0,1,0) above character (a separate follow transform in LateUpdate) | same | [V `CameraThirdPerson.LateUpdate`, prefab] |
| FOV | **40** (lens) | **50** (`Factory_Camera._defaultFOV`, applied at Start; prefab lens 40) | [V `CFG/Game.Factory_Camera.asset` ME only] |
| Near/Far | 0.75 / 500 | 0.5 / 500; per-zone far clip override (`CameraFarDistanceZone._farDistance`, default 200) | [V prefab, `CameraFarDistanceZone.cs`] |
| Binding mode | 5 = SimpleFollowWithWorldUp (carpet: WorldSpace) | **4 = WorldSpace** | [V prefab m_BindingMode] ME camera does not yaw with character [I] |
| Drag input | X axis max speed **700** (wrap -180..180, no invert); Y axis max speed **10** (0..1, invert on), `m_AccelTime/m_DecelTime` 0.1 | same | [V prefab] |
| Look sensitivity | `PlayerControl._lookSensitive` **6** (prefab; code default 20); touch delta = `e.delta / Screen.dpi` | 6 | [V `Player.prefab`, `Player_Escape.prefab`, `PlayerControl.cs`] |
| Pitch limits | Y axis 0..1 mapped over 3 orbits (top h6 -> bottom h-5) [I derived] | | |
| Collision | CinemachineCollider radius 0.1, MinDistanceFromTarget 0.1, strategy 0, damping 0 | same | [V prefab] |
| Pinch zoom | `_maxUserZoom` 3 in CameraThirdPerson | `CameraPinchZoom`: zoomSpeed 0.01, scroll 2, max 3; only right-half touches | [V `CameraPinchZoom.cs`] |
| Occluder fade | no | `Camera_OccluderFade`: ray cam->player NonAlloc(32), alpha 0.25, fade 0.15 s on `Camera_OccluderFadeTarget` | [V] |
| Shake | `CameraShaker.Shake(amp 0.4, freq 3.5, dur 0.2)`, `ShakeDecay(decay 2/s)`, lerped shake | same | [V `CameraShaker.cs`] |
| Cinematic | `CameraFollowPath`: DOTween `DOPath` cubic bezier, 1 s per waypoint, delay 1 s, FreeLook disabled | not present | [V `CameraFollowPath.cs`, `Tower_Master`] |
| Teleport warp | `FreeLook.ForceCameraPosition` via `CameraManager` (delay 1 frame UniTask) | adds `WarpForTeleport(delta, rotation)` using `OnTargetObjectWarped` | [V] |

Why camera numbers are identical: ME forked KT prefab and kept zero damping [I]. Zero damping + 1000 sharpness character = "locked, snappy" Roblox feel.

### 2.4 Input (touch)
- Move: Joystick Pack `Joystick` component (`Assets/Packages Required/Joystick Pack`), axes from `PlayerGUI.JoystickMove`, keyboard fallback `Input.GetAxis("Horizontal"/"Vertical")` [V `PlayerControl.cs`, `PlayerGUI.cs`]. Keyboard-latch logic `_isWaitingKeyboardRelease` for mode switches [V].
- Look: right-side `UIPointerDrag` -> `delta/DPI * _lookSensitive` [V]; arrow axes `HorizontalArrow/VerticalArrow` on desktop [V].
- Action: `UIPointerClick` down/up; jump is **edge-triggered** `_inputActionConsumed` (one jump per press) [V]. Tap while on carpet = "carpet off + jump" (`_requestJumpAfterCarpetOff`) [V].
- Camera-relative move: `_cameraPlanerRotation = LookRotation(ProjectOnPlane(camRot*forward, up))` applied to clamp-1 input [V KC L634-700].
- ME differences: separate Jump and Swing buttons (`GoSwingAction`), no poison inversion, jetpack removed, tutorial events (`TutorialActionPressed/SwingPressed`), `CurrentMoveInput` exposed [V `ME PlayerControl.cs` diff].
- KT: Poison effect inverts input; booster JetPack replaces jump with jetpack hold [V].

---------------------------------------------------------------------------
## 3. Character system

### 3.1 States
- `Character_State`: KT `Alive/Ragdoll/Dead`; ME `Alive/Dead` [V `Character.cs`].
- `CharacterKC.State` (a `StateMachine<State>` used as a state holder; the logic is `switch (CurrentState)` inside KCC callbacks, not per-state classes) [V `KC/CharacterKC.cs` L500-520]:
  - KT: `Default, Freeze, ClimbingLadder, Jumping, Jetpack, FlyCarpet, Treadmill, Stop`
  - ME: adds `WallJump`, `Swing` (10 states) [V ME `InitStateMachine`].
  - Ladder sub-state `StateClimb {Enter, Middle, Exit}`.
- `Character_Monkey_State {Moving, AutoTraining}` (ME only), `Character_Monkey_Type {Npc, Player, Boss}` [V].
- `Character.IsGrounded` = `CurrentState == Default`; `EventGroundedChanged` from state change [V].

### 3.2 KCC callback pipeline (template-worthy)
`SetInputs(ref struct)` (clamps input, projects camera plane, sets `_jumpRequested`) -> `BeforeCharacterUpdate` (carpet/jetpack/ladder state switches) -> `UpdateRotation` -> `UpdateVelocity` (ground lerp / air accel+gravity+drag / jump / ladder / carpet / jetpack) -> `AfterCharacterUpdate` (jump-buffer expiry, `_jumpConsumed` reset on stable ground, coyote timer) -> `PostGroundingUpdate` (`OnLanded` / `OnLeaveStableGround` delayed 0.5 s via PrimeTween delay) [V KC L634-1500].
Jump rule: `canGroundJump = !consumed && (stable || timeSinceAbleToJump <= postGrace)`; applies `v += up*jumpUpSpeed*jumpVerticalMultiplier - project(v, up)` and `ForceUnground(0.1)` [V KC L1190-1230].

### 3.3 Trampoline (physics landing hook)
`CharacterKC.ProcessTrampolineCollision` (called from `OnGroundHit`): modes `Multiplier` (bounce height = fall height x **1.5**, min fall **0.5 m**, repeat bounce at least 5 m) or `ExactHeight` (**5 m**); required velocity `sqrt(2*g*h)`; `ForceUnground(0.25)`, velocity applied after 0.05 s delay, posts `Event_Trampoline_Bounced`; also a capsule probe fallback at landing [V KC L1535-1634; `Platform_Trampoline.cs` defaults].

### 3.4 Death, revive, fall
- `CharacterFallDetector.Tick`: reset `_groundY` while stable/climbing; if `groundY - y > threshold(20)` -> `Character.Kill()` (optional raycast-ground veto) [V].
- Revive after `Factory_Character.ReviveDelay` (2 s) at checkpoint transform; `Character_Dead` swaps skin for ragdoll prefab (player only), restores on revive [V `Character_Dead.cs`].
- KT-only: `Character_Ragdoll` (CharacterJoint ragdoll, `_explodeForce` 1000, radius 10), ragdoll get-up by joystick when checkpoint <= 0, `Character_Attack` (power 10, overlap buffer 32, vertical tolerance 2, check interval 0.15, hit delay 0.25 s), `Character_Effect` (Burning/Freeze/Poison), `Character_Item` (weapon/coil), `Character_FNAFTower` (minigame mode), `Character_Squid` [V file lists/greps].

### 3.5 Skins
`Character_Skin_Asset` SO (name, `Character_Skin_Type`, unlock currency/price, IAP id, dailyLogin, `ReferencePrefab`, shared mesh cache) [V `Character/Skin/Character_Skin_Asset.cs`]. Types: KT `Normal, Squid, Brainrot, AntMan, Transfomer, VIP, All`; ME `Normal, Squid, VIP, All` [V]. `Character_Renderer` loads the skin prefab and fires `EventSkinLoaded/EventSkinBeforeReleased`; children (Wing, Tail, Carpet) re-attach on that event [V]. `Character_Skin_Switcher` (zone: trigger posts `Event_Character_Skin_Equip(asset, character)`, editor `Generate()` button instantiates preview at scale 2) [V]. Animator params via `HashDictionary`: IsJumping, IsJumpingDouble, IsClimbing, ClimbY, VelocityZ, SpeedMultiplier, IsHeroLanding, MotionType, AttackType/Motion, TriggerAttack [V `Character_Animator.cs`], with `...IfExists` guards so skins with missing params do not warn.

### 3.6 KT vs ME difference summary (Character)
| Aspect | KT | ME | Why |
|---|---|---|---|
| Config source | global SO singleton | SO profile + per-minigame override | ME has Escape vs Obby feel [V assets] |
| Extra states | none | WallJump, Swing, Sink | ME is an obby/swing game [I] |
| Speed | constant 4.5 | level-scaled | ME is a speed-training game (treadmill) [V] |
| Ragdoll/combat | yes | stripped | KT is a brawl/obby hybrid with weapons [V] |
| Slope limit | 60 | 89 | ME slope-obby [I] |

---------------------------------------------------------------------------
## 4. Player (`L/Player`)
- `Player : MonoSingleton<Player>` (not persistent) owns refs to `Character`, `CameraManager`, `PlayerGUI`, `PlayerControl`; registers `GameStatic.Player`; subscribes cutscene, booster, trampoline, gacha, home-return events; carpet fuel UI per frame if `Factory_Carpet.UseFuelSystem`; ragdoll follow + get-up gating (`AllowGetUpDelay` 1 s, settle velocity 2 m/s) [V `KT Player.cs`]. ME Player is 295 lines: no ragdoll, adds `SetSpeedFOVBoost` forwarding and bottom-rig swap on carpet [V].
- `Player_Floor_Tracker` (KT) tracks tower floor; `Player_SpeedSliderFeedback` (both, 207 lines): speed-slider UI with `_visibleDuration` 1 s, `_fadeDuration` 0.15 s [V].
- Camera lifecycle: `CameraManager` (MonoSingleton) listens `Event_Character_Revive` (player) and `Event_Camera_Reset` and re-places camera at `character.TransformPoint(_offset (0,10,-20))` next frame [V `CameraManager.cs`]; applies `DevicePolicy.ApplyCameraPolicy` (disable PP/depth on low-end) [V].

---------------------------------------------------------------------------
## 5. AI / bots (`L/AI`, `L/Navigation`)

### 5.1 Structure
`AI : MonoCachedFast` (KT 504 lines, ME 415) with `AI_Component` children (Avoidance, Follow_Waypoint, Attack, Battle, Renderer) and `AI_Manager` spawner [V]. Driver writes `CharacterKCInputAI {MoveVector, LookVector, Jump}` in `Update` then `Controller.SetInputs(ref _input)`; poison inverts; `ExternalMove` override; clears input while traversing a nav link [V `AI.cs` L110-150].

### 5.2 States (`AI_State`, `StateMachine<AI_State>` with state objects implementing `IStateMachine`)
- ME: `Stop, Idle, Chase` [V `ME AI/State/AI_State.cs`].
- KT: `Stop, Idle, Chase, Carpet, Battle_MoveToArea, Battle_Frenzy, Battle_PatrolInsideArea, HideToSafeZone, Morph, BattleRoyal_*, StealAPet_*, SKB_Boss_State_*` (many minigame modes; only Idle/Chase/Carpet/Morph/Stop registered in base `InitStateMachine`, Battle states in `AI_Battle`) [V `KT AI_State.cs`, `AI.cs` L150-175].
- `AI_Type`: KT `Parkour, Battle, PatrolCarpet, BattleRoyal, StealAPet, SpeedKeyboard_Npc, Boss`; ME base type + `MonkeyEscape_AI` configurator [V].
- Chase state: `OnUpdate { _AI.JumpIfNecessary(); if (_AI.MoveToGoal(UsePathfinding)) OnComplete?.Invoke(); }` (Idle/Chase raise `OnComplete`; `AI_Follow_Waypoint` listens and advances) [V `AI_State_Chase.cs`].

### 5.3 Waypoint-follow brain (core of "bots that run the course")
- `AI_Waypoint` (graph node: `_next[]`, type Normal/WaitForDistance/Morph, cell `_x,_z`, reach radius, `IsReachedExpanded(pos, speed, 0.5)`), `AI_Waypoint_Manager` (spatial grid `_cellSize` **15**, `_maxUpwardHeightDelta` **7.5**, `_heightPriorityWeight` **6**, nearest-waypoint lookup) [V].
- `AI_Follow_Waypoint`: advance when reached; `_useWaypointCrossingAdvance`/`_useSpeedExpandedReach` flags for high-speed modes; **stuck check every 5 s** teleports/rewinds; abandon waypoints > 8 m higher only in SpeedKeyboard [V `KT AI_Follow_Waypoint.cs` L15-136].
- `MonkeyEscape_AI` config: `UsePathfinding = true`, `UseVelocityReached = true`, pass-through + speed-expanded reach on, level randomised `levelMin + rand(0.._randomLevelRange=5)` each revive, `IsPreventLevelUp` [V `ME MonkeyEscape_AI.cs`].
- Rubber-banding: Parkour/SpeedKeyboard bots **teleport (revive at checkpoint around player)** if checkpoint index differs by > `Factory_AI.TeleportIfFartherThan` (**5**) [V `AI.cs` L137-149, `CFG/Game.Factory_AI.asset`]; `GetCheckpointAroundPlayer(range 3)` [V].
- Jump heuristics (`AI_Avoidance`): three cached-per-frame NonAlloc raycasts in character local space: block `(0,0.1,0)->(0,1,1)`, fall `(0,0.5,0.4)->(0,-0.5,0.4)`, kill `(0,0.1,0)->(0,0.1,1)`; `Jump = obstacleAhead || fallAhead || obstacleKill`; never jump while `ClimbingLadder` [V `AI_Avoidance.cs`, `AI.JumpIfNecessary`]. Ladder detection by BoxCast 0.8 m ahead [V].
- Aggression (KT): `AIProbAttackPlayer` 0.25, `...OnBattleArea` 0.25, `ParkourRangedWeaponChance` 0.15, `AttackRangeOverlapse` 5, per-minigame overrides array [V `CFG/Game.Factory_AI.asset`, `Factory_AI.cs`].
- Spawning: `AI_Manager` spawns `Device_Policy.ScaleAICount(_count=5)` one per frame, registers a loading-screen task [V `AI_Manager.cs`]. Low-end scales bot count [V].

### 5.4 Navigation
| | KT | ME |
|---|---|---|
| Pathing backends | `AI_Pathfinding` abstract + `AI_Pathfinding_Astar` (A* Pathfinding Project `AIPath`, `maxSpeed = StableMoveSpeedMax`) **and** `AI_Pathfinding_AgentNavigation` (ProjectDawn Agents Navigation, ECS, NavMesh) [V] | only `AI_Pathfinding_AgentNavigation` [V] |
| Link types | `Nav_AstarPath_Link` (NodeLink2, snaps to graph/ground, default ground mask 805307905 = layers 0,9,10,28,29) + `Nav_TraversalLink` (NavMeshLink) + `Ladder_NavmeshLink` [V] | `Nav_TraversalLink` + `Ladder_NavmeshLink` [V] |
| Link traversal | `Character_AgentLinkTraversal`: scripted parabola; `duration = dist/speed`; no arc if dist <= **5**; else height `v^2/2g + dist*0.01`; ease in-out curve; requires AgentNavMeshAuthoring LinkTraversal = Custom (warns otherwise) [V `Character_AgentLinkTraversal.cs`, identical 133 lines both] | same |
| Sync | agent body position/velocity overwritten from KCC motor each LateUpdate so the nav agent never fights the controller [V `AI_Pathfinding_AgentNavigation.LateUpdate`] | same |
| Editor tool | `NavTraversalLinkEditor` window: click two scene points -> NavMeshLink with snap, bidirectional, container [V `Scripts/Editor/NavTraversalLinkEditor.cs` both] | same |
Why two backends in KT: A* used by `+1Speed` stage prefabs (SpeedKeyboard flat keyboards), AgentNavigation for obby/tower [I from prefab grep: `AIPath` only in `Prefabs/+1Speed/...`]. ME dropped A* [V manifest/no code].

---------------------------------------------------------------------------
## 6. Boss / hazards / obstacles
| System | Files | Behaviour / numbers |
|---|---|---|
| ME Boss | `Boss/Boss_SimpleTransformMove` (`Patrol`/`Chase` enum, `SimpleState : IStateMachine`), `Boss_TargetDetector` (trigger volume) | no pathfinding: patrols a rect inside parent bounds (`_patrolRangeX` 1, `_patrolRangeZ` 0.5, padding 10%), patrol speed **2**, chase speed **4**, rotation smoothness 6, arrival 0.1; kills on contact via `OptCollisionRegister` [V] |
| KT Boss | `AI_Type.Boss`, `SKB_Boss_State_Patrol/Chasing` in `AI_State` | boss AI uses full AI state machine; skips revive hook (`if Type==Boss return`) [V `AI.Character_EventRevive`] |
| `PlatformKill` | `Killer_Type` Obstacle/Enemy/Boss/Other/ObstacleBypassImmortal=101 | trigger -> `Character.Kill(type)` [V] |
| Obstacles KT | `Obs_GreenRedLight` (doll head rotate 0.5 s, shoot line, bullet), `Obs_JumpRope` (+`_ButtonSpeed`, moveDown 0.01/0.15 s), `Obs_Mingle`, `Obs_CollisionPushOut` | Squid-Game minigames [V] |
| Interactive KT | `Interactive_Button_On/Off/Fade` (press 0.2 m in 0.1 s, release buffer 0.08, min hold 0.15), `Interactive_Raycast_Input` (tap raycast 100 m, ignore left 50% of screen), `Interactive_Caculator*` (math door puzzle: digits/operand ranges, max 6 input digits) [V] |
| ME Triggers | `Trigger_Character_Event` (Player/Npc/All mode, triggerOnce, cooldown, UnityEvent), `Trigger_Character_Sink` (sinkSpeed 0.5, jumpMultiplier 0.5 -> quicksand/mud via `CharacterKC.EnterSinkZone`), `Trigger_Open_Popup` [V] |

---------------------------------------------------------------------------
## 7. Platforms (`L/Platform`)
All reactive platforms derive `OptCollisionRegister<ICharacterCollidable>` (no per-platform `OnTriggerEnter/GetComponent`) [V].

| Platform | Mechanic & numbers | Project |
|---|---|---|
| `Platform_Trampoline` | see 3.3; press visual 0.2 m / 0.1 s (OutQuad) then OutBack, SFX random from array | both |
| `PlatformConveyor` | each stable character gets `AddVelocity(dir * velocity * dt)` with `_velocity` **700** (per-second scale; AddVelocity is an impulse added once per frame), optional move-boost 700, moving-against uses `BaseVelocity.XZ * Factory_Config.PlatformConveyorMovingAgainstMultiplier`; `_size` scales the belt mesh Z | both |
| `PlatformFade` / `Platform_Fade_Countdown` | fade out 0.75 s, reappear delay 2 s, fade in 0.75 s; countdown variant 3 s (warning colour red, fade 0.2 s, keep-in 1 s) with TMP text | both |
| `Platform_Glass`, `Platform_Glass_Bridge` | breakable pane `_respawnDelay` 2 s; bridge of segments (`_segmentCount` 3, spacing 0.1) L/R pairs, one pane safe (Squid-Game bridge) | both |
| `Platform_Breakable` (273 lines) | break-on-touch with timer | both |
| `Platform_Move` + `PlatformAction` | KCC `PhysicsMover` + `IMoverController` driven by `AnimationSequence`; action buttons toggle sequences/hide | both |
| `PlatformForceZone` | constant push `_forceSpeed` **10** along `_forceDirection` (local default up) | ME |
| `Platform_WallJump` | modes `OneJump`/`Infinite`, min up force **25** (override 20), blinking highlight 0.35 s; KC constants: cooldown **0.5 s**, wall contact grace **0.12 s**, forward probe **0.75 m**, rising horizontal control x0.18, control ramp 1.5 s | ME |
| `Platform_Swing` (+ `CharacterKC.Swing`) | rope pendulum: rope limit **8 m**, input accel **30**, gravity x1, damping **0.5**, idle damping 0.5, **max tangential speed 60**, steering sharpness 3, flip assist 1.5 above speed 10, release jump up **8** + forward boost **2**, min hold 0.3 s, input buffer 0.12 s, rope retract 0.75 s / extend 1.25 s, acquire scoring forward weight 130 / distance penalty 0.015 | ME |
| `PlatformKill` | kill trigger (lava/spikes) with `Killer_Type` | both |
Platform-specific KC hook knobs: `AddVelocity` (conveyor, force zones), `ForceUnground`, `EnterSinkZone`, `ProcessTrampolineCollision`, `Swing.API` (`BeginSwing/ReleaseSwing`) [V].

---------------------------------------------------------------------------
## 8. Ladder, Checkpoint, Teleporter, Tower, Treadmill

### 8.1 Ladder
`Ladder : MonoCached` (BoxCollider, `_height`, optional tiled `_modelPrefab` with `_modelHeight`; static `Dictionary<Collider, Ladder>` cache + `Collider.IsLadder(out)` extension) [V `Ladder.cs`]. Entry: BoxCast detection in KC (section 2.1); Enter lerps to ladder surface at padding 0.2, Middle climbs `input.z * climbSpeed`, exits over top (`y > Height`) to `Exit` lerp forward by padding+0.1; jump input detaches backwards at `-StableMoveSpeedMax` [V KC L1250-1305]. `Ladder_NavmeshLink` lets bots path onto ladders [V]. Static cache is not reset on domain reload - add `RuntimeInitializeOnLoadMethod` in clones [I].

### 8.2 Checkpoint
`ICheckpoint {Index, Transform}`; `Checkpoint : OptCollisionRegister` posts `Event_Checkpoint_Enter`, player-only: if `_index > Data_Checkpoint.Value` save + `PlayFx` (particle, sfx, `Taptic.Success`); `Checkpoint_Manager : MonoSingleton` array + `Checkpoint_Static` queries (`GetCheckpointPlayer/Next/Previous/AroundPlayer(range)/Nearest`, `GetMode.Clamp|Loop`, `CheckpointCount` DataValue) [V `Checkpoint/*.cs`]. `Character_Checkpoint.Now` DataValue tracks each actor's index (bots too); player respawn = `Revive_Checkpoint` event -> set position+rotation at checkpoint, `Event_Camera_Reset` [V]. ME: `Checkpoint._ground` transform, `Character_Checkpoint_Escape/_Obby` subclasses, `Minigame_Checkpoint_Provider` [V].

### 8.3 Teleporter
`Teleporter : OptCollisionRegister`: paired (`_otherTeleporter`) or `_destination`; fade out 0.2 s / fade in 0.2 s via UniTask; static `s_teleportingCharacters` + per-instance `_waitingForExitCharacters` to prevent ping-pong until the character exits the collider; saves/restores control state per character (`ControlState`) [V `Teleporter.cs`]. Camera warp afterwards (ME `WarpForTeleport`).

### 8.4 Tower (KT only)
`Tower_Manager : MonoSingleton` (checkpoints array, floors, `Turn {Index, Angle}` data, cached BoxCollider bounds, sets `Minigame_Static.Type`, `Checkpoint_Static.CheckpointCount`), `Tower_Checkpoint` (ICheckpoint), `Tower_Floor {_height}` + `Tower_Fall_Detector` (trigger -> `Character.SetTowerFloor`), `Tower_WinDetector`, `Tower_Master` (intro cutscene: wait loader idle, `CameraFollowPath.Follow` bezier over `_cameraPath`, then posts `Event_AI_ConstructAllowed`) [V].

### 8.5 Treadmill (ME)
`Treadmill : OptCollisionRegister` (types Normal/Candy/Chocolate/Admin/VIP/IAP_x10/God/Infinity/x200/x20K/Special; unlock Free/Reward/Cup/IAP/Subscription; `_speedMultiplierStr` compact-number string; slots, focus); entering sets `Character_Monkey_State.AutoTraining` + `CharacterKC.State.Treadmill` (force-run anim, jump blocked, no trained speed carried, movement limited to base) [V `Treadmill.cs`, KC L1596-1700, L1896]. `Character_Treadmill_Manager` spawns fake runners (`Character_Treadmill`) that swap random skins every **90-120 s** (staggered first load over 1.5 s) to fake multiplayer [V]. `Treadmill_AdsBreak` polls 1 s; `Treadmill_Button` UI for run/buy/ads states [V].

---------------------------------------------------------------------------
## 9. Cosmetics: Pet, Wing, Aura, Trail
| System | Structure | Numbers/behaviour |
|---|---|---|
| Pet (KT) | `Pet : OptCollisionRegister` + `Pet_Movement/Animator/Renderer/Component`, `Pet_Updater` static registry ticked from `GameManager.Update(dt)` (HashSet + remove buffer, try/catch per pet) | straight-line seek: `_moveSpeed` **3**, `_rotateSpeed` **240 deg/s**, arrive 0.1 m; `MoveTo(dest, speed)`; collidable (steal-a-pet mode); 498-line `Pet.cs` includes editor prefab-bake helpers (`PrefabContentsScope`) [V] |
| Wing (KT) | `Wing_Asset` SO (`_jumpMutiplier` **2**, prefab, thumbnail), `Wing_Data` (unlocked), `Wing_Zone` trigger posts `Event_Wing_Equip/Unequip` (uses `OptScriptLookup.TryFindFirst`), `Character_Wing` binds to skin loaded/released + item weapon `IncludedWing`; adds/subtracts `JumpVerticalMultiplier` | skin types Brainrot excluded [V] |
| Aura (ME) | `Aura_Asset` SO (`_multiplier` **1.5**, IAP/dailyLogin/entropy price "100"), `Aura_Provider : SerializedMonoBehaviour` `Dictionary<Aura_Asset, GameObject>` of pre-baked visuals on the skin; `Data_Aura` equipped name; `Event_Character_Aura_Equip` | visual toggled, not instantiated [V] |
| Trail (ME) | same pattern (`Trail_Asset` `_multiplier` 1.5, price "50", `Trail_Provider.Activate` clears TrailRenderers/particles) | NPCs get random trail/aura, changed every `AI_REVIVES_PER_AURA_CHANGE` = 20 revives [V `Character_Monkey.cs`] |
Multiplier semantic: aura/trail `_multiplier` scale XP/speed gain (`Character_Monkey` tick multiplies `_speedLogicMultiplier * treadmillPoint * expMultiplier * (1+boost)`) [V/I].

---------------------------------------------------------------------------
## 10. Cross-project diff (why)
| Topic | KT | ME | Reason |
|---|---|---|---|
| Speed feel | fixed 4.5 | 4.5 + 0.5/level, FOV kick | ME = idle "speed train" loop [V] |
| Jump | 11 | 11 / 16.5 per minigame | per-minigame SO override [V] |
| Camera FOV | 40 | 50 + speed boost to 60 | sense of speed [V Factory_Camera] |
| Camera bind | SimpleFollowWithWorldUp | WorldSpace | ME steer relative to world/camera [I] |
| AI states | many modes | Stop/Idle/Chase + waypoint | ME bots only run the course [V] |
| Pathing | A* + AgentNavigation | AgentNavigation | consolidation [V] |
| Collision dispatch | `OptCollisionRegister<ICharacterCollidable>` | same | perf rule in global CLAUDE.md [V] |
| Combat | Attack/Ragdoll/Items | none | genre [V] |

---------------------------------------------------------------------------
## 11. Code skeletons worth templating
1. **KCC controller shell**: `partial class CharacterKC : MonoBase, ICharacterController` + `enum State` + `StateMachine<State>` switch dispatch + Factory-backed property accessors (`float _x => Factory_CharacterKC.X`) + `SetInputs(ref struct)`. Keep `Add`/`Multiplier` layers (`StableMoveSpeedAdd * SpeedLimitFactor`, `JumpVerticalMultiplier`, `FallGravityMultiplier`) so shop/booster/wing/level systems never mutate base values.
2. **Input structs**: `CharacterKCInputPlayer {moveAxisForward, moveAxisRight, cameraRotation, jumpDown, jetpackDown}` / `CharacterKCInputAI {MoveVector, LookVector, Jump}` -> one `SetInputs` overload each.
3. **Collidable world object**: `class X : OptCollisionRegister<ICharacterCollidable>, ICharacterCollidable` with 4 tiny callbacks; `Character : OptCollisionSensorFast<ICharacterCollidable>` forwarding; `OptScriptLookup.Register(this, colliders)` in Awake.
4. **Fall detector + revive loop** (`CharacterFallDetector`, `Character_Dead`, `Checkpoint_Static`).
5. **Zone static-with-deepest-wins** (`CameraFarDistanceZone`: static active list, `RuntimeInitializeOnLoadMethod` reset, pick deepest interior).
6. **FreeLook player camera prefab**: 3 orbits (6/1, 3/6, -1/3), zero damping, follow transform one unit above the pivot, input via `m_XAxis.m_InputAxisValue` from `delta/DPI*sens`.
7. **Waypoint bot**: `AI`+`AI_State_Idle/Chase`+`AI_Follow_Waypoint`+`AI_Avoidance` (3 raycasts) + `AI_Waypoint_Manager` grid; rubber-band teleport by checkpoint index distance.
8. **Nav link authoring tool** (`NavTraversalLinkEditor`) + `Character_AgentLinkTraversal` parabola.
9. **Trampoline physics** `v = sqrt(2 g h)` with delayed apply and double-bounce guard.
10. **Provider-dictionary cosmetics** (`Dictionary<Asset, GameObject>` of pre-baked children, activate/deactivate).

Gotchas observed [V]: orientation sharpness field is dead tuning (hard-coded 100); 0.5 s coyote/buffer very forgiving; ladder cache static not reset; ME Escape and Obby profiles differ only by x1.5 scalar (derive from one base).

---------------------------------------------------------------------------
## 12. Proposed classification

| # | Candidate | Class | Proposed name | Must contain (3-6) |
|---|---|---|---|---|
| 1 | Feel table + conversion math | **DATA** | `docs/data/roblox-feel-table.md` (+ link from `roblox-character-camera`) | speed 4.5, g 30, jump 11 => 2.02 m, grace 0.5/0.5, sharpness 1000, FOV 40/50, orbits 6/1,3/6,-1/3, zero damping, look sens 6, fall threshold 20, revive 2 s; formula `v=sqrt(2gh)`; Obby x1.5 scale |
| 2 | KCC character controller | **RECIPE** | `kcc-character-controller` | KCC package setup (capsule 0.3/1.7/0.85, step 0.5, slope 60-89); State enum + callback pipeline (section 3.2); SO-profile tuning (`CharacterKC_Asset` + override); Add/Multiplier layers; jump buffer/coyote rule; input struct bridge |
| 3 | Player camera | **RECIPE** | `freelook-third-person-camera` | Prefab values table 2.3; follow-transform-in-LateUpdate; `UpdateInput` axis wiring; FOV speed boost with release; far-clip zones; occluder fade; carpet/scale rig multipliers; teleport warp |
| 4 | Touch input bridge | **SKILL** (extend `mobile-input-controls`) | `mobile-input-controls` + `references/kt-me-input.md` | Joystick Pack + `UIPointerDrag/Click`; `delta/DPI*sens`; edge-triggered jump; keyboard fallback; reset on focus/dead; separate Jump/Swing buttons |
| 5 | Collision-registry rule | **RULE** | `collidable-registry-rule` (fold into `mobile-perf-audit`) | `OptCollisionRegister<ICharacterCollidable>` for every world object; sensor on mover only; empty callbacks; reset statics with `SubsystemRegistration`; no `GetComponent` in triggers |
| 6 | Reactive platform kit | **RECIPE** | `platform-kit` | trampoline (Multiplier 1.5 / Exact 5, min fall 0.5), conveyor (`AddVelocity`, 700), fade (0.75/2/0.75), glass bridge, force zone 10, kill zone `Killer_Type`, PhysicsMover moving platform; KC hooks needed |
| 7 | Ladder | **RECIPE** | `ladder-climb` | Ladder collider+height+cache; BoxCast probe 0.05 s; Enter/Middle/Exit lerps; jump-off; bot nav link; reset static cache |
| 8 | Checkpoint + respawn loop | **RECIPE** | `checkpoint-respawn` | `ICheckpoint`, manager+static queries (Clamp/Loop), `Data_Checkpoint` save only on higher index, `Character_Checkpoint.Now`, fall detector 20 m, revive 2 s, camera reset event, FX/sfx/haptic |
| 9 | Bot brain (waypoints) | **SKILL** (extend `npc-bots-and-enemies`) | `npc-bots-and-enemies` + `references/waypoint-bots.md` | AI state enum + `IStateMachine` states; waypoint graph + grid manager (15/7.5/6); 3-ray avoidance; stuck 5 s; rubber-band teleport range 5; spawn one-per-frame with loader task; low-end count scaling |
| 10 | Nav links + traversal | **TOOL** | `nav-traversal-link-tool` | EditorWindow (two clicks, snap mask, bidirectional, container); `Nav_TraversalLink` snap; `Character_AgentLinkTraversal` parabola rules (<=5 m walk, `v^2/2g+0.01d`); agent-sync LateUpdate |
| 11 | Teleporter | **RECIPE** | `teleporter-pad` | paired/destination, 0.2/0.2 fades via UniTask, anti-ping-pong exit tracking, control-state save/restore, camera warp |
| 12 | Treadmill / speed training | **RECIPE** | `treadmill-speed-training` (in `roblox-genre-patterns`) | `Treadmill_Type/Unlock_Type`, AutoTraining state, force-run anim, tick 0.15 s earn, base-speed cap, fake runner skins 90-120 s, per-level speed 0.5 + jump 0.1 formula |
| 13 | Rope swing / wall jump (advanced movement) | **RECIPE** | `kcc-advanced-movement` | Swing constants (section 7), WallJump constants, sink zone, force zone; each as extra `State` + `partial class` file; tutorial hooks |
| 14 | Cosmetic slots (aura/trail/wing/pet) | **RECIPE** | `cosmetic-slot-providers` | Asset SO (multiplier, price, IAP, dailyLogin) + `Data_*` equipped + `Event_*_Equip` + provider dictionary of baked visuals + wing jump multiplier layer; pet tick via static updater |
| 15 | Boss patrol/chase | **RECIPE** | `simple-boss-patrol-chase` | rect patrol (X 1, Z 0.5, pad 10%), speeds 2/4, detector trigger, `IStateMachine` inner state, kill via registry |
| 16 | Tower/obby cutscene intro | **RECIPE** | `intro-camera-flyover` | `CameraFollowPath` bezier (7.5 radius, 1 s/waypoint), freelook toggle, UI hide events, bot construct event |
| 17 | Character-driver parity rule | **RULE** | `same-character-different-driver` (fold into `npc-bots-and-enemies`) | bots use player prefab with `Type.Npc`; AI writes same input struct; clear input during nav link; poison inversion example |
| 18 | Tuning-by-profile rule | **RULE** | `config-driven-feature` addendum | base SO + override SO per minigame, never mutate singleton at runtime except via add/multiplier layers (KT setters mutate the singleton: anti-pattern, ME avoids with profiles) |
| 19 | Fixes/gotchas list | **DATA** | `docs/data/kcc-gotchas.md` | dead orientation field, 0.5 s coyote, static ladder cache, orbit bottom override, `AirSteeringSpeedPoints` |

Open items / not verified: Fixed Timestep value and KCC interpolation settings; exact Joystick variant on `PlayerGUI`; contents of `Character_Skin.cs` in KT (1030 lines) and `Character_Attack.cs` internals were only skimmed; Cinemachine Y-axis starting value not read.
