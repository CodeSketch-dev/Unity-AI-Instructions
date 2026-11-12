# 19 - Character skins, avatar, rigs, animation, bots, shop preview

Scope: how skins are defined/applied, rigs, animation sets, accessories, ragdoll, bots-as-players, crowd budgets, 3D shop preview, and a proposed character platform. Read-only mining, nothing compiled or run. Tags: **[V]** verified in cited file, **[I]** inferred. Paths: KT = `knife-tower/knife-tower-troll-unity/Assets/_Game`, ME = `monkey-escape/monkey-escape-unity/Assets/_Game`, CT = `climb-and-jump-tower/climb-tower-unity/Assets/_Game` (legacy), PX = `problox/Assets/4_Game_HungryWorm/Scripts`, SAE = `steal-an-egg/Assets/vanhuy_probloxengine`.

## 1. Findings per project

### 1.1 knife-tower (primary)
| Topic | Finding | Tag |
|---|---|---|
| Skin definition | `Character_Skin_Asset : ScriptableObject` (258 lines): `_skinName`, `_type` (`Character_Skin_Type`), `_avatar`, `_thumbnail` sprites, `_unlockType` (`Currency_Type`: Free/Gem/IAP_NoneConsumable/IAP_Subscription/...), `_unlockPrice`, `_iapProductId`, `_dailyLoginOnly`, `_infoWeapon` (Brainrot only), `_referencePrefab`, `_useSharedMesh`, read-only `_cachedMesh/_cachedMaterial`. ID = asset `name` (`Character_Skin_<Name>`) | V `Scripts/Logic/Character/Skin/Character_Skin_Asset.cs` |
| Skin data | Persisted per skin as `CharacterSkinData {bool _isUnlocked}` in `Data_Character : DataBlock` `Dictionary<string,CharacterSkinData> _skins` + `DataValue<string> _equipped` + `_lastNormalEquipped`; `Get(id)` does `TryAdd` lazily; `Init()` ends with `Factory_Character.Bake()` | V `Scripts/Data/Data_Character.cs`, `CharacterSkinData.cs` |
| Data pitfall | `SetEquipped` silently no-ops if the id was never registered by touching `asset.Data` (documented in asset comments); Free skins auto-unlock on first `Data` read; subscription skins ignore the persisted flag (live entitlement) | V `Character_Skin_Asset.cs` |
| Registry | `Factory_Character` (Odin singleton): `_skinDefault`, arrays `_skinNormal/_skinSquid/_skinBrainRot/_skinTransformer/_skinVIP`, single `_skinAntMan`, runtime `_skinDictionary` + `AllSkin`; `SetAllowedSkinType(s)`, `GetRandomSkin(type)`, `GetEquipped()`, `FallbackSkin()` | V `Scripts/Factory/Factory_Character.cs` |
| Counts | 137 files under `Prefabs/Character/Skin/*` (sub-folders Brainrot, Parkour, Squid, ...), 22 `Character_Skin_*.asset` in `Configs/Character/Parkour`, more in Brainrot/Transformer/VIP | V `ls` |
| Skin prefab | Root `Character_Skin_<n>` with `Character_Skin` MonoCached + nested FBX prefab instance (Animator, SkinnedMeshRenderer, bones), "Lucky Box" holder, 12 Rigidbody + 11 CharacterJoint ragdoll parts baked into every skin prefab, Animator `CullingMode 2` (CullCompletely), UpdateMode 0 | V `Prefabs/Character/Skin/Parkour/Character_Skin_1.prefab` greps |
| Skin component | `Character_Skin` serialized "Must Have": config, Animator, SkinnedMeshRenderer, ragdoll camera follower; optional: mainBody, `Character_Ragdoll`, `Item_Container_Tag`, `CarpetController`, `LuckyBoxHolder`, `OutlineController`. Also hosts stealth fade, freeze material swap, focus tint, color override, wing instance; runtime material instances are created for effects and released in `OnDestroy` | V `Scripts/Logic/Character/Character_Skin.cs` |
| Apply path | `Character_Renderer` subscribes `StaticBus<Event_Character_Skin_Equip>`; `e.Character == null` means broadcast to player. `LoadSkin`: first load or different `Type` -> `Instantiate(ReferencePrefab)`; same type + `UseSharedMesh` -> **swap `sharedMesh` + `sharedMaterials` on the existing SMR** (no instantiate, no rebind; only valid when skeleton is identical). Fires `EventSkinBeforeReleased` / `EventSkinLoaded`; Animator, Wing, Tail, Carpet, Item components re-bind on `EventSkinLoaded` | V `Scripts/Logic/Character/Character_Renderer.cs`, `Character_Animator.cs` |
| Minigame override | `GetRuntimeSkin` forces Transformer/VIP to `SkinDefault` during SpeedKeyboard event (type gating per mode) | V `Character_Renderer.cs` |
| Switcher | `Character_Skin_Switcher : OptCollisionRegister<ICharacterCollidable>`: trigger posts `Event_Character_Skin_Equip(asset, character)`; editor `Generate()` instantiates the reference prefab at scale 2, disables `Character_Skin` and its Animator (static display) | V `Character_Skin_Switcher.cs` |
| Animator contract | Params via `HashDictionary`: IsJumping, IsJumpingDouble, IsClimbing, ClimbY, VelocityZ, SpeedMultiplier, IsHeroLanding, MotionType, AttackType, AttackMotion, HasWeapon, IsHolding, TriggerAttack. `Character_Animator` caches `animator.parameters` per animator into a `Dictionary<int, ParameterType>` and only writes if the param exists (skins with different controllers do not warn); animator speed = base x named speed sources | V `Character_Animator.cs` |
| Controllers | `_Art/3D/Character/Animator/Parkour/{Character_Parkour,Character_VIP,Character_Event}.controller`, `Brainrot/Character_<Name>.controller` (one per brainrot skin, own animations) | V `find` |
| Ragdoll | `Character_Ragdoll`: `Part[] {Transform, Rigidbody, Collider}` plus CharacterJoint arrays, parallel caches, `SetRagdoll(active, duration, ease)` via PrimeTween sequence (blend animator pose to ragdoll and back), `AddForce` explode force 1000 radius 10; `Character_Skin.ActiveRagdoll` guards re-entry and calls `RecoverAnimatorPose()` (`Animator.Update(0)`) on exit | V `Character_Ragdoll.cs`, `Character_Skin.cs` |
| Accessories | Wing: `Wing_Asset` SO, `Character_Wing` re-attaches on skin loaded, instantiated under skin root, disallowed for Brainrot. Weapons via `Item_Container_Tag` hand holder + `Item_Activator` created from `Factory_Item`, gated by `IsSkinAllowEquipItem` (Normal/Squid only). No hair/hat/face slot system | V `Character_Skin.cs`, catalog 04 |
| Shop UI | `Shop_Skin` (375 lines): builds an item list from `Factory_Character.SkinVIP` then `SkinNormal`, one `Shop_Skin_Item` per asset in a ScrollRect, selection through `StaticBus<Event_Shop_Skin_Item_Selected>`, **preview is a 2D `Image.sprite = Thumbnail`** (not 3D), action buttons per unlock type (Ads, DailyLogin, IAP sub, IAP single, Equip/Equipped), scroll-focus helper, `CancelToken`, symmetric (un)subscribe | V `Scripts/Logic/Shop/Skin/Shop_Skin.cs` |
| 3D preview (the only one) | `Shop_Trail_Preview` uses Kamgam `WorldImage`: spawns a random Normal skin at `(10000,0,0)` far from play space, `AddWorldObject`, `CameraFollowTransform = true`, animator fed `VelocityZ`, moves forward at 5 m/s with `animator.speed = 10`. `WorldImage` renders a world object camera into a RenderTexture inside a uGUI Image; defaults FOV 60, clear-to-color alpha 0, culling mask -1, depth 0, optional `CameraOverride` / `RenderTextureOverride` | V `Logic/Shop/Trail/Shop_Trail_Preview.cs`, `Kamgam/UGUIWorldImage/.../WorldImage.cs`. Drag-rotate: not found in game code [I: WorldImage has rotate/drag members but not used by Shop_Skin] |
| Bots as players | AI characters use the same `Character` + `Character-AI.prefab`; skins random from `Factory_Character.GetRandomSkin/SetAllowedSkinTypes`; `AI_Manager` spawns `Device_Policy.ScaleAICount(5)` one per frame behind a loader task; fake runners in ME swap random skins every 90-120 s | V `Prefabs/Character/Character-AI.prefab` exists; V catalog 04 sections 5.3, 3.x |
| Nametags / emotes | No nametag or emote system found: `Character_UI` is a world-space effect icon + countdown following the skin (`position = follow + _offset` in `LateUpdate`) | V `Character_UI.cs`; grep for emote/nametag found only unrelated files |

### 1.2 monkey-escape (primary)
- Trimmed fork of KT: same `Character_Skin_Asset`, `Character_Skin_Switcher`, `Character_Renderer`, `Event_Character_Skin_Equip/Unlocked`; types Normal/Squid/VIP/All; no combat/ragdoll partials (V catalog 04 section 3.5; file list `Scripts/Logic/Character`).
- Adds `Scripts/Core/SkinnedMesh_Bone_Binder.cs`: **editor tool that rebinds an SMR to a target skeleton by bone name**, with `Validate Bone Mapping` and `Bind To Target Skeleton` context menus, sets `rootBone`, `bones`, `updateWhenOffscreen` (V). This is the closest existing "new-skin import validation", but it is per-renderer, manual, and has no batch/local batch runner mode.
- Aura: visuals pre-baked on the skin and toggled, not instantiated (V catalog 04 section 4).

### 1.3 climb-and-jump-tower (legacy, ideas only)
- `CharacterSkin : MonoCached` with `Animator`, `Renderer[]`, per-body-part markers `CharacterSkin_Body` (`HandLeft/HandRight/FootLeft/FootRight`) for attaching FX/gear to limbs; `TurnOffShadow()` for non-player skins (`shadowCastingMode Off`, `receiveShadows false`); HSV shift property `_HsvShift` for tinting; **`render.material` in `Awake` duplicates materials per renderer** (anti-pattern) (V `Scripts/Logic/Character/Skin/CharacterSkin*.cs`).
- Config asset `CTJ_CharacterSkin_Config` numbered `1_..12_CharacterSkin_Character_NN_Name Variant.asset` with sort-order unlock chain (`CanUnlock` by sort order, coin cost, energy) (V `Configs/Minigame/ClimbTowerJump/CharacterSkins`, `CharacterSkin_Shop_Preview.cs`).
- Shop preview is again a 2D `Thumbnail` image. `FTS_Character_Skin_Shop_Showroom.prefab` exists (Root + showroom name) but contains no Camera/RenderTexture/Light entries in the grep, so it is a static display stage, not a live-render stage [V file only partly inspected; I on purpose].
- bike-obby: `Prefabs/Character/Character_Skin.prefab` + `Model/Character_Skin_Boy_01..` prefabs, shop thumbnails `skin1.png`; scenes binary (V find).

### 1.4 problox / ride-a-pet / steal-an-egg
| Project | Finding | Tag |
|---|---|---|
| problox (HungryWorm) | Worm "skin" = `CharacterSkinConfig` SO: icon, name, `AssetReference _headPrefab` + `_tailPrefab` (**Addressables**), `SkinUnlockType {Currency, Ads}`, `_adsRequiredToUnlock`, `_tailColor`, `_speedPointBonus` (gameplay stat on skin), auto-assigned `_id`; data via `CharacterSkinDataBlock` (`Player` DataValue<int> + per-id data); `CharacterSkinPreview` loads head/tail with `Addressables.InstantiateAsync`, a `_loadVersion` counter drops stale async loads, releases with `ReleaseInstance`; `CharacterSkinStand` = world pedestal (collidable) that destroys itself once unlocked; `PlayerAvatar` shows config icon on `EventValueChanged`. | V `PX/Character/Skin/*.cs`, `Player/PlayerAvatar.cs` |
| ride-a-pet | `Game.Characters.SkinConfig` SOs `SO_Skin 1..14` (ID, UnlockType, `_moneyCost`, Product, `_legacyCupCost`, Avatar, Thumbnail, prefab) in `Configs/Skin`; skin class lives in a package outside `_Game/Scripts` | V `Configs/Skin/SO_Skin 1.asset` |
| steal-an-egg | Not Spine for characters: `Base_VanHuy.CharacterSkin` is a **modular avatar**: `AvatarCategory {Avatar,Clothes,Accessories,Body}` x `AvatarSubCategory {Items,Tail,Bag,Hair,SkinColor,Jewelery,Face,Hat}`, `AvatarPartDatabase` per slot + `AvatarSetDatabase` (full outfits), part prefab carries `AvatarPart` + `BoneMapper` (stores root bone name, bone name list, saved bounds; `TryLoad()` re-resolves bones by name under the character and resets SMR local transform). `EquipShopItem` previews without saving; `SaveEquippedLook()` persists; `UnequipShopItem` returns to pool; `CharacterVisibility` fades via per-instance materials switched to Transparent at runtime; `RagdollController` and `PlayerDieBreak` are siblings. The Spine folder is only a vendor import (no Spine skin scripts found) | V `SAE/1_BaseEngine/Scripts/Base_Scripts/SkinCharacter/*.cs`, `HFramework/Scripts/Update_Root/BoneMapper.cs`, `Player/CharacterVisibility.cs` |

### 1.5 Key lessons
1. Two skin architectures exist: **whole-prefab skin** (KT/ME/CT/bike-obby/ride-a-pet; one prefab per skin, cheap to author, heavy per variant) and **modular avatar** (steal-an-egg; slot parts bound to a shared skeleton by bone name). A Roblox GDD with hats/hair/clothes needs the modular path; one with "buy a character" needs the whole-prefab path. Both can share one skeleton contract.
2. Fast skin switch: **same skeleton + shared mesh/material swap** (KT `UseSharedMesh`) avoids instantiate and animator re-bind. It must be gated by a validated "same skeleton" flag, not trusted by hand.
3. Preview is 2D in 3 of 4 projects: a baked thumbnail sprite is the cheapest correct default; live 3D is only needed for rotation/animation previews (WorldImage far-away spawn pattern).
4. Gaps nobody solved (must be designed): nametags, emotes, per-skin LOD, crowd budget numbers, import validation, avatar thumbnails auto-rendering, ragdoll cost control (KT bakes 12 rigidbodies + 11 joints into every skin).

## 2. Anti-patterns to forbid
- `renderer.material` / `.materials` in `Awake` for every skin (CT `CharacterSkin.Awake`, SAE `CharacterVisibility`): per-instance material copies break batching and leak. Use shared materials plus MaterialPropertyBlock for 1-2 values, or create runtime material copies lazily only for the single effected character and destroy them (KT does this for stealth/freeze and releases in `OnDestroy`).
- `GetComponentInChildren<Animator>` lookups at runtime (KT `Character_Skin.Animator` is lazy but the fallbacks exist); prefer serialized refs filled by the import tool.
- Ragdoll rigidbodies enabled on every bot skin; keep disabled/kinematic and bake only on the player and nearest N.
- Unreachable preview data: `_cachedMesh/_cachedMaterial` caches that need an editor `Validate` button (KT) go stale silently; the import tool should always refresh them.
- `SetEquipped` that silently ignores unknown ids (KT) - fail loudly in editor.

## 3. Proposed character platform

### 3.1 Data model (house style, `namespace Game`)
```
Character_Skin_Asset : ScriptableObject          // one per skin, Assets/_Game/Configs/Character/<Type>/
  string ID (= asset name, validated unique)
  string DisplayKey                              // localization key, not literal text
  Character_Skin_Type Type                       // game-defined enum, default Normal/VIP/Event
  Character_Rig_Asset Rig                        // shared skeleton contract (see below)
  GameObject Prefab                              // validated variant of Character_Skin_Base
  Sprite Thumbnail, Avatar                       // baked by tool
  Currency_Type UnlockType; double Price; string IapId; bool DailyOnly; int Order
  float SpeedBonus, JumpBonus (optional stat hook, from problox _speedPointBonus)
  bool UseSharedMesh (derived by tool, read-only) // true only if skeleton hash equals Rig.SkeletonHash
  int TriangleCount, BoneCount, MaterialCount, TextureBytes (read-only, written by validator)
  string ImportReportGuid                        // link to last validation report
Character_Rig_Asset : ScriptableObject           // one per skeleton family (Humanoid-R15-like, Pet, ...)
  string[] RequiredBones (name list, ordered), string RootBone, Avatar (Humanoid) or Generic flag
  int SkeletonHash (hash of ordered bone names), RuntimeAnimatorController Controller
  string[] RequiredParams (name, type) from the animation contract
  Slot[] Slots {AvatarSubCategory-like id, BoneName, LocalOffset}   // hat, hand_r, back (wing), tail, name_tag
  int MaxBones (<= 30 default), Bounds LocalBounds
Factory_Character : ScriptableObjectSingleton    // existing pattern: arrays per type + Dictionary<string,asset> built in OnInitialize, duplicate-id check
Data_Character : DataBlock<Data_Character>       // unchanged shape: Dictionary<string,CharacterSkinData>, DataValue<string> Equipped, LastNormalEquipped; plus Dictionary<string,string> EquippedParts (slot -> partId) for modular avatar
Character_Part_Asset (optional, modular games)   // slot, prefab with SkinnedMeshRenderer, bone name list baked at import (BoneMapper idea), price
Event_Character_Skin_Equip(asset, character)     // existing; add Event_Character_Part_Equip(slot, asset, character)
```
Rules: ID = asset name; `Data` access always registers the id; equip of an unlocked id only; unknown id logs an error in editor (fixes KT silent no-op).

### 3.2 Runtime components
- `Character_Renderer` (existing): load by type; shared-mesh swap only when `Rig.SkeletonHash` matches and `UseSharedMesh`; otherwise instantiate from a pool keyed by skin id (pool 1 per active skin; bots reuse).
- `Character_Skin` (existing): refs filled by tool (`Animator`, main SMR, Slot transforms dictionary built once into a small array), stealth/freeze effects optional and lazy.
- `Character_Slots` (new, small): resolves `Rig.Slots` to transforms on skin load; wings, weapons, hats, tails, auras, nametag anchor attach by slot id, never by `Find`.
- `Character_Nametag`: single world-space TMP on a shared pooled canvas or `TextMeshPro` (3D) reused; enabled only inside a near `CullingGroup` band, hidden for far bots (see budgets). Text set only on change.
- `Character_Emote` (if GDD needs): emotes are Animator triggers on an emote layer with a fixed param `EmoteId` (int) plus `TriggerEmote`; clips authored per rig, whitelist in `Rig.RequiredParams`; UI wheel posts `Event_Character_Emote(id, character)`.
- Ragdoll: player and the nearest N (<= 3) characters only; ragdoll parts live on a separate pooled `Character_Ragdoll` prefab per rig that is spawned at death and fed the pose (KT already swaps skin for a ragdoll prefab on death; `Character_Dead`), instead of 12 rigidbodies baked into every skin.
- Bots-as-players: bots use the same `Character` prefab and `IStateMachine` brain; skin chosen from `Factory_Character.GetRandomSkin` through an `AllowedSkinTypes` list; nametags from a name list; spawn one per frame behind a loader task; teleport rubber-band per catalog 04.

### 3.3 Animation contract
- One `RuntimeAnimatorController` per rig family, stored in `Character_Rig_Asset`; skins reference the rig, not their own controller. Override controllers only for brainrot-like special rigs (KT has one controller per brainrot skin: allowed as `AnimatorOverrideController`).
- Fixed parameter set (hashed once in a `HashDictionary` style static class): `Speed` or `VelocityZ` (float), `IsGrounded` (bool), `IsJumping` (bool), `IsJumpingDouble`, `IsClimbing` (bool), `ClimbY` (float), `IsSwimming` (bool, if used), `MotionType` (float), `HasWeapon` (bool), `AttackType`/`TriggerAttack`, `EmoteId` (int) + `TriggerEmote`, `IsDead`/`TriggerHit` (trigger). Names are not renamed per skin.
- Required clips (state names): Idle, Run (blend by Speed), Jump, Fall, Land, Climb, Dead/Hit, Win, plus optional Emote_01..N. Missing optional params are tolerated (`...IfExists` guard as in `Character_Animator`).
- Animator settings: `CullingMode` = CullCompletely for bots and far characters (KT skin prefabs use 2), player AlwaysAnimate; `UpdateMode` Normal; apply root motion off; no animator on pure display skins unless needed (KT `Generate()` disables Animator).
- Humanoid vs Generic: Generic + shared bone-name skeleton is cheaper and keeps bone-name rebinding simple; Humanoid only if retargeting external mocap clips is required. Pick per rig in the asset.

### 3.4 New-skin import validation tool (Editor, batch-capable)
Name: `Character_Skin_Importer` (menu `Tools/Character/Validate Skin` + `-executeMethod` entry + MCP-callable static method). Input: FBX/prefab path + target `Character_Rig_Asset` + type. Steps and fail conditions:
1. Hierarchy: exactly one Animator (or none for static), one root, no nested Cameras/Lights, no missing scripts.
2. Skeleton: ordered bone names equal `Rig.RequiredBones` (report missing/extra); compute `SkeletonHash`; if equal, mark `UseSharedMesh = true`; if not, run `SkinnedMesh_Bone_Binder`-style rebind by name (ME script) into the base skeleton or fail with the diff.
3. Mesh budget: triangles, vertex count, bones per vertex <= 4, bone count <= `Rig.MaxBones`, skinned mesh count <= 2, readable flag off, normals/tangents/colors only if shader needs them, import compression on.
4. Materials: <= 2 materials, shared material from the project's character material family, shader name allow-list (SRP Batcher compatible, one `_BaseColor`/`_BaseMap`), no alpha blend unless declared, textures <= 512x512 (256 for bots-only), ASTC, mipmaps on, atlased in one texture where possible.
5. Animator: controller equals rig controller or valid override; all `RequiredParams` present (typed); culling mode set; `Animator.avatar` valid.
6. Bounds: SMR `localBounds` set, `updateWhenOffscreen` false, quality bones 2-4 per project tier.
7. Ragdoll: none on skin prefab (provided by shared ragdoll prefab per rig); collider-free skin prefab.
8. Slots: all `Rig.Slots` transforms resolvable on the skeleton.
9. Auto-fix: write refs (Animator, SMR, slots) into `Character_Skin`, set Layer, shadow modes (off for bots, per CT `TurnOffShadow`), create `Character_Skin_Asset` in `Configs/Character/<Type>/`, register in `Factory_Character`, refresh stats.
10. Thumbnail bake: render a transparent PNG from a preview stage (see 3.5) at 256x256 into `Assets/_Game/Art/UI/Characters/`, assign `Thumbnail/Avatar`. Output a JSON report `Library/CharacterImport/<id>.json` (pass/fail per rule) consumed by a hook and by the production pipeline; failures block `Factory_Character` registration.
Should be a deterministic C# editor script (TOOL), not hand-edited YAML; asset creation via Unity MCP calls into it.

### 3.5 Shop 3D preview stage (design; only KT trail preview provides a precedent)
Default recommendation: **baked thumbnails** (what KT/CT/problox use); upgrade to live 3D only for "rotate to inspect" requirements.
Live stage rig (single scene object, `Character_Preview_Stage`, prefab under `Prefabs/UI/Shop`):
- Placement: far from play space (KT uses `(10000,0,0)`), own layer `UI_Preview` excluded from the main camera culling mask and all gameplay lights.
- Camera: one dedicated Camera, perspective FOV 25-30 for characters (WorldImage default 60 is too wide), culling mask = `UI_Preview` only, clear flags SolidColor alpha 0, `HDR` off, MSAA off, no post volume, depth only if needed, disabled when the shop is closed.
- Output: `RenderTexture` 512x512 (256 on low tier), `RenderTextureFormat.ARGB32`, depth 16, no mipmaps, no MSAA, assigned to a `RawImage` in the popup (Kamgam `WorldImage` already does this: `UseRenderTexture`, `CameraOverride`, `RenderTextureOverride`). Release the RT in `OnDisable`/`OnDestroy`.
- Light: one directional light with `Culling Mask = UI_Preview`, no shadows; rim light optional via a second light only on high tier.
- Stage object: skin spawned from the pool at stage origin, scale 1, Animator on with Idle, `CullingMode AlwaysAnimate` while visible, `Character_Skin` effects disabled; swap skin through the same `LoadSkin` path used in game (async if Addressables).
- Drag-rotate: pointer-drag handler on the RawImage rotating the stage pivot `rotationY += delta.x * 0.4`, with inertia damping 6 and snap back after 2 s; touch-drag only on that rect so ScrollRect for the item list is not blocked.
- Lifecycle: show -> enable camera/RT -> spawn; selection event `Event_Shop_Skin_Item_Selected` triggers `Show(asset)`; hide -> release skin to pool, disable camera. Version token to drop stale loads (problox `_loadVersion`).
- Unlock-state visuals: locked = black silhouette using a single flat material swapped via shared material, not property-block per renderer.

## 4. Performance budgets (low-end Android; all INFERRED targets until measured on device)
| Item | Budget | Basis |
|---|---|---|
| Player skin | <= 3,000 tris, <= 25 bones, <= 2 materials, 512 px texture | I (typical blocky Roblox-style; KT sample numbers not measured) |
| Bot/crowd skin | <= 1,500 tris, <= 20 bones, 1 material, 256 px texture, shared material | I |
| Visible animated characters | <= 12 full-rate Animators at once; the rest CullCompletely or update every 2nd-3rd frame | I; KT uses CullCompletely V |
| Bot count | Use `Device_Policy.ScaleAICount` (KT/ME base 5, scaled by tier) | V catalog 04 |
| Skinned mesh batching | Total skinned draw calls from characters <= 25; same material across all bots | I |
| Ragdoll | player + nearest 3 only; shared pooled ragdoll prefab; ragdoll rigidbodies <= 14 per rig; auto-sleep 3 s | I; KT today 12 RB + 11 joints per skin V |
| Shadows | blob/none for bots (CT `TurnOffShadow` V), real shadow only on player | V/I |
| Nametags | max 8 visible, `CullingGroup` band 25 m, text set on change only, shared font atlas | I |
| Per-skin memory | mesh+texture <= 1.5 MB; pool one instance per skin id; unload unused addressable skins on shop close | I |
| Shop preview | one RT 512x512 (256 low), camera enabled only while visible, no per-frame allocations | I |
| Instantiate | never in gameplay loop; skin spawn behind loader or one-per-frame (V `AI_Manager`) | V |
| Crowd LOD | distance bands: 0-15 m full, 15-40 m 20 fps animator (`animator.speed` stepped or manual `Update`), >40 m renderer off via `CullingGroup` | I |
Measure with Unity Profiler on a mid device; do not state gains without measurement.

## 5. Hooks and checks (for the pipeline)
- Pre-commit/local batch runner check: run Skin Importer in `--report-only` over `Assets/_Game/Prefabs/Character`; fail on any non-pass.
- Hook: block creating a `Character_Skin_Asset` whose `Prefab` has `SkinnedMeshRenderer.material` access in its scripts or has Rigidbody children.
- Static check: every `Character_Skin_Asset` present in `Factory_Character` and in the shop list; every `Thumbnail` assigned; unique IDs.

## 6. Proposed classification

| Type | Proposed name | Must-haves |
|---|---|---|
| RULE | `character-rig-and-animation-contract` | 1) one `Character_Rig_Asset` per skeleton family with ordered bone names and `SkeletonHash`; 2) fixed Animator parameter names/types in a static hash class, missing optional params tolerated; 3) controller owned by rig, override controllers for specials; 4) culling mode CullCompletely for bots; 5) no `renderer.material` or per-skin duplicated materials; 6) slot transforms resolved by id, no `Find` |
| RULE | `character-perf-budgets` | 1) tri/bone/material/texture caps for player vs bot; 2) animator/ragdoll/shadow/nametag limits with numbers; 3) crowd LOD bands via `CullingGroup`; 4) ragdoll only player + nearest N from shared pooled prefab; 5) no instantiate in loops, one-per-frame bot spawn; 6) "measure on device before claiming" |
| SKILL | `character-skin-system` | 1) `Character_Skin_Asset` + `Character_Rig_Asset` + `Factory_Character` + `Data_Character` chain with Equip/Unlock events; 2) `Character_Renderer.LoadSkin` with shared-mesh swap gated by skeleton hash; 3) unlock types (Free/Gem/IAP/Ads/Daily/Subscription) as one enum plus entitlement rule; 4) register-on-access data pitfall and fail-loud equip; 5) type-gating per minigame; 6) bots pick from allowed skin types |
| SKILL | `shop-skin-preview` | 1) default baked-thumbnail shop (list + selection event + action buttons per unlock type); 2) live 3D stage rig: layer, camera FOV 25-30, 512 RT, own light, far origin, drag-rotate handler; 3) pool/release lifecycle and stale-load token; 4) camera/RT disabled when hidden; 5) locked silhouette material; 6) hand-off to `unity-ui` popup anatomy |
| RECIPE | `modular-avatar-parts` | 1) `AvatarCategory/SubCategory` slot enums and `Character_Part_Asset`; 2) bone-name binding (BoneMapper idea) baked at import, runtime `TryLoad`; 3) preview equip without save, `SaveEquippedLook` on buy; 4) set vs part items; 5) pooled part prefabs; 6) per-slot capped tri budget |
| RECIPE | `bots-as-players` | 1) same `Character` prefab, AI driver writes input struct; 2) random skin + name from lists, nametag budget; 3) spawn one per frame with loader task, count scaled by `Device_Policy`; 4) fake-runner skin swap every 90-120 s (ME treadmill); 5) rubber-band teleport rule; 6) low-LOD animator culling |
| RECIPE | `character-emotes-nametags` | 1) `EmoteId` int + trigger on emote layer, whitelist in rig; 2) `Event_Character_Emote`; 3) emote wheel UI uses popup/anchor rules; 4) single world-space nametag with `CullingGroup` band, text on change; 5) colour/outline for local player vs others; 6) localized default names |
| TOOL | `character-skin-importer` | 1) deterministic Editor + batch entry, JSON report; 2) skeleton diff and bone-name rebind (reuse `SkinnedMesh_Bone_Binder` logic); 3) mesh/material/texture/animator/bounds checks with numeric limits; 4) auto-wire `Character_Skin` refs, create asset, register in `Factory_Character`, refresh stats; 5) thumbnail bake from preview stage; 6) callable through Unity MCP and local batch runner, blocks registration on fail |
| DATA | `character-catalog.json` (+ `Character_Rig_Asset` instances) | 1) rig definitions (bones, slots, params, max bones); 2) skin rows (id, type, unlock, price, iap, order, budgets); 3) allowed skin types per minigame; 4) bot name list; 5) emote list per rig; 6) validation thresholds per device tier |

## 7. Open questions / caveats
- No project here has measured per-skin triangle counts or on-device animator cost; all budgets in section 4 are INFERRED starting points.
- The CT `FTS_Character_Skin_Shop_Showroom.prefab` was only grepped (no camera/RT keys found); treat it as not a live stage until opened in Unity.
- Spine: no skin scripts found in steal-an-egg; the "Spine" folder appears to be the vendor runtime only (I).
- KT `Shop_Skin` has no 3D preview; the only 3D preview precedent is the trail preview using Kamgam WorldImage (V).
- Nametags and emotes have no precedent in the mined projects; the section 3.2 designs are new.
