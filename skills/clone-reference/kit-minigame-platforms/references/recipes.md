# Minigame recipes R1-R8 and the 10-step new-mode flow
Illustrative; verify API names in the installed SketchEngine package.

## 7. Build a new minigame in 10 steps

1. Decide family number and add the `Minigame_Type` enum value (sparse number, e.g. 301).
2. Create scene `Minigame_<Name>`; add `GameSingleton` (persistent root) and your `Player` prefab (reuse the shared Character prefab; only fork for camera/UI).
3. Add an empty `Minigame_Master` object with `_type`; add per-mode switches in `Initialize()` only if needed (weapons, trail, skin pool).
4. Add `Minigame_GUI_Loader` object; author your HUD as a View prefab (copy `Minigame_GUI_View`: Root > SafeArea) and register it as an Addressable; assign `_viewGUIReference`.
5. Add `BGMKickOff` with an `AudioConfig` for the minigame BGM.
6. Drop the `Minigame_SceneCombiner` prefab (mesh combine, distance cull, waypoint manager) and, for bots, `AI_Manager`; add `Ads_InterstitialBreak` if the mode has interstitial pacing.
7. Build the map from prefab chunks: platforms (`Platform_Fade/Conveyor/Trampoline/Kill`), obstacles (`Teleporter`, buttons), checkpoints (`Tower_Manager` + `Tower_Checkpoint[]` or `Checkpoint_Manager`), win trigger (`Tower_WinDetector`).
8. Create `Configs/Minigame/<Name>.asset` (`Minigame_Selection_Asset`: type, title, thumbnail, scene, load type, AI spawn config) and press "Add to Build Settings".
9. Add the asset to `Factory_Minigame._minigames`; run Home: the card appears automatically (data-driven list, remote sort order).
10. Verify: enter from Home card, die (revive flow branches on the type), reach a checkpoint (saved per type), win, back to Home; re-enter 3 times (scene teardown: all `StaticBus` unsubscribed, `Minigame_Master.OnDestroy` resets overrides).

---

## 11. Genre-tagged recipes (supersede section 8 examples)

Genres: COLLECTOR (throw/collect pets, catch loops), TYCOON (idle income with stations), RUNNER (endless or lane runner), PARKOUR (tower/obby).

### R1. Register a new game mode (fits: ALL)
Steps: enum value, scene, selection asset, add to factory list, mode master in scene. Every mode is "a scene + one asset".
- COLLECTOR: `PetCatch` scene (pens + throw zone), `LoadingScreen` load type for many pet prefabs.
- TYCOON: `Factory` scene; weapons disabled through the policy function.
- RUNNER: `Run` scene; checkpoint = distance milestone saved as int.
```csharp
// Provenance: Factory_Minigame.Get / Minigame_Selection_Asset.Switch. SketchEngine: ScriptableObjectSingleton + scene loader.
public static void Enter(Mode_Type t) {
  var a = Factory_Mode.Get(t);          // dictionary built in OnInitialize
  Data_Mode.GetEnter(t).Value++;        // persisted counter (FTUE, analytics)
  a.Switch();                           // reset globals, load scene
}
```

### R2. Mode shell with per-mode policy functions (fits: ALL)
Put every "does this mode allow X" in a static policy class keyed by the current type; set the type in the master `Awake` so Start-time systems see it. Never scatter `if (mode == ...)`.
- COLLECTOR: `AllowThrowWeapon`; TYCOON: `AllowJump`; RUNNER: `ResetProgressOnEnter`.
```csharp
// Provenance: Minigame_Static policy functions.
public static class Mode_Static {
  public static DataValue<Mode_Type> Type = new(Mode_Type.Run);
  public static bool IsWeaponAllowed(Mode_Type t) => t != Mode_Type.Factory;
  public static bool ShouldResetProgressOnEnter() => true;
}
```
Why: a Start-time inventory restore once re-enabled weapons over the mode setting; one source of truth fixed it.

### R3. Persistent progress marker / checkpoint (fits: RUNNER, PARKOUR, COLLECTOR, TYCOON)
Bring `ICheckpoint`, a data dictionary keyed by mode type, a trigger that saves the max index when the PLAYER enters, and a router when two modes use different managers.
- RUNNER: checkpoint each 500 m. TYCOON: "zone unlocked" index at a new area door. COLLECTOR: "pen level reached".
```csharp
// Provenance: Tower_Checkpoint.OnTriggerEnterFunc (player only, index must grow).
public void OnTriggerEnterFunc(Actor a) {
  if (!a.IsPlayer) return;
  var saved = Data_Checkpoint.Get();
  if (_index <= saved.Value) return;
  saved.Value = _index; PlayFx(); Toast("Checkpoint!");
}
```

### R4. Contact registration (fits: ALL)
Actor owns the physics callbacks; world objects derive from the framework collision register and implement an actor-family interface. No `GetComponent` in callbacks; empty bodies for unused ones (skill `collision-registry`).
- COLLECTOR: pen gate, pickup bubble. TYCOON: stall counter, collect pad. RUNNER: coin, obstacle, boost pad.

### R5. Hazard / penalty zone (fits: RUNNER, PARKOUR, COLLECTOR arenas)
`PlatformKill` shape: trigger calls `actor.Kill(type)` unless immortal; keep a bypass type for hazards that ignore shields. A "penalty zone" replaces `Kill` with `ApplyPenalty` (lose coins).

### R6. Mover / bouncer / conveyor / breakable (fits: RUNNER, PARKOUR, COLLECTOR arenas, TYCOON belts)
- Mover: sequence evaluated inside the mover controller so riders inherit motion (KT uses KinematicCharacterController `PhysicsMover`; otherwise kinematic Rigidbody + `MovePosition`).
- Bouncer: platform = feedback only, physics hook in the actor controller (fall height or exact height).
- Conveyor: `AddVelocity(dir*v*dt)` in FixedUpdate for grounded actors, optional move-direction boost; in a TYCOON replace `Character` with a product item and keep the same dispatch.
- Breakable: precomputed splinters, re-arm on revive event.

### R7. Teleporter pair (fits: ALL spatial maps)
TYCOON stations to hub, COLLECTOR hub to arena, RUNNER checkpoint warp. Keep the in-progress static HashSet, the wait-for-exit set (prevents ping-pong), control lock and `finally` restoration.

### R8. Death / revive branching (fits: RUNNER, PARKOUR; simplified in COLLECTOR; skip in TYCOON)
One `ResultDead` in the player class: no progress means silent respawn (+ interstitial placement `type.ToDeath()`); progress > 0 means revive popup via `Factory_Result` branching on mode type.

Mapping of old section-8 recipes: A to R1, B to R2, C to fade tile (parkour and party arenas only), D to R5, E to R6, F to R7, G to R3, H to R8.

### What not to change (lessons from history)
- Sparse enum numbers are save keys: add, never renumber.
- Keep `Minigame_GUI_Loader` ordered before BGM starters.
- Keep cancellation and unsubscription in OnDestroy of every shell/platform script (many KT fixes were teardown leaks across repeated scene entries).
- Do not import keyboard/typing code to get a generic moving platform; extract the 80-line concept.
