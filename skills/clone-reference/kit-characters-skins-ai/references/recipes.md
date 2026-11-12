# Character kit recipes R1-R8 and dependency closure
Illustrative code; verify API names in the installed SketchEngine package.

## 8. Dependency closure for reusing the character stack
Minimum for "actor + swappable skin + equip + save":
1. Scripts: `Character`, `Character_Component`, `Character_Renderer`, `Character_Skin`, `Character_Skin_Asset`, `CharacterSkinData`, `Character_Skin_Type`, `Data_Character`, `Factory_Character`, `Event_Character_Skin_Equip/Unlocked`, `ICharacterCollidable`, `ICharacterEventSource`, `Character_Static`, `Character_Animator` + `HashDictionary`, `OutlineController` (optional).
2. Movement: `CharacterKC` + `KinematicCharacterMotor` (KCC package) + `Factory_CharacterKC` (or any controller exposing the same events).
3. Assets: Character prefab, Skin base prefab, one rig FBX + controller + masks, `Configs/Character/*.asset`, `Factory_Character` singleton asset, materials/shader (OmniShade or project one).
4. Optional layers: Dead/Ragdoll/Fx/Sfx/Effect/UI/Checkpoint/Wing/Trail/Item, shop (`Shop_Skin`, `Shop_Skin_Item`), IAP (`Currency_Type`, subscription).
5. Do not bring: tower/minigame statics referenced inside (`Minigame_Static`, `SKB_*`, `Tower_*`); cut them or replace by an injected policy.


## 10. Kit recipes (SketchEngine-first wording; KT only as provenance)

Genres key: A = humanoid avatar/obby-parkour, B = collector/pets (owned followers), C = idle tycoon, D = runner, E = enemy/bot shooter.

### R1. Swappable skin on a universal actor (A, B, C, D) 
Bring: `Actor` (physics-sensor owner), `Actor_Renderer`, `Skin` prefab, `SkinAsset` SO, `Data_Skins` DataBlock, `Factory_Skins`, `Event_Skin_Equip`.
```csharp
public class Actor_Renderer : Actor_Component {
  [SerializeField] Transform _mount; Skin _skin;
  void Awake()  => StaticBus<Event_Skin_Equip>.Subscribe(OnEquip);
  void OnDestroy()=> StaticBus<Event_Skin_Equip>.Unsubscribe(OnEquip);
  void OnEquip(Event_Skin_Equip e){ if (e.Actor ? Actor==e.Actor : IsPlayer) Load(e.Skin); }
  public void Load(SkinAsset a){ if(!a) return;
    if(_skin && a.SharedRig && a.Type==_assetType){ _skin.SwapMeshMaterial(a.Mesh,a.Material); }
    else { if(_skin) Destroy(_skin.gameObject); _skin=Instantiate(a.Prefab,_mount).GetComponent<Skin>(); _skin.Bind(Actor); }
    Loaded?.Invoke(_skin); }
  public event Action<Skin> Loaded;
}
```
Genre use: A humanoid with outfit prefabs; B each owned pet is an Actor with a pet skin asset (follow target set by owner); C staff/customer avatars. Why: one physics/gameplay prefab, art swapped by data; save key = asset name. Do not change asset names after release.

### R2. Skin asset + unlock + shop item (A, B, C)
SO fields: id=name, type, thumbnail, UnlockType (Free/Ads/Gem/IAP/Subscription), price/IAP id, `IsUnlocked` (subscription = live entitlement), `Unlock()` -> `Data.Unlock()` + `Event_Skin_Unlocked`, `Equip()` -> `Data.SetEquipped(id)` + `Event_Skin_Equip`. Shop cell subscribes to both events and shows locked/equipped frames (refs/p2_characters). Pets: same SO as "pet species" with rarity.

### R3. Animator contract with guarded parameters (A, D, E)
Define a static hash table; cache `animator.parameters` per animator; setters skip missing or wrong-type params and inactive animators; push state with a per-tick diff-check; combine speed multipliers through named sources. Lets monsters/pets with partial controllers share one driver.

### R4. Bot spawner by tier (E, A, D, B ambient crowd)
`BotManager` prefab in scene reads `{tier -> {BotType: count}}` from the level/minigame asset, spawns bots staggered (one per few seconds) with a cancel token, places on random waypoints, bot = `Actor` variant with reduced controller options + `StateMachine<BotState>`. Teleport bots near the player's progress marker instead of simulating long routes; never reload their skin on death.

### R5. Trail / aura cluster toggled, not spawned (A, D, C vehicles)
Prefab `Trail_Provider` with a `Dictionary<TrailAsset, GameObject>` of disabled children; equip event -> deactivate old, `Activate(new)` (clear TrailRenderer/Particles). `Fx_Trail` exposes `SetTime/SetWidth`. Burst fx (death, level-up) = child `Fx_ToggleEmit`; global one-shots = hub that `Emit`s from one hidden instance.

### R6. Checkpoint + revive (A, D, E)
`ICheckpoint {Index, Transform}`; checkpoint prefab = trigger registered in the collision registry, posts `Event_Checkpoint_Enter`; save max index in a per-mode `DataValue<int>`; manager assigns indexes from hierarchy order in an editor button; revive event teleports to checkpoint and resets camera. For runners use it as a respawn segment marker; for tycoon as "area unlocked" marker.

### R7. Skin pad / preview in world (A, B)
Trigger pad with `Skin_Switcher` posts equip event; display variant shows thumbnail + name on a world canvas, group script prevents re-wearing within a cluster. Pets: pad = "adopt/equip this pet" display.

### R8. Overhead status UI (B, C, E)
World-space canvas child that follows `actor.position + cachedOffset` (or the ragdoll follower), shows one icon + remaining seconds; set text only when the integer second changes. Use for pet name/level tags (not in KT: add a name text beside the icon) and enemy debuffs.

