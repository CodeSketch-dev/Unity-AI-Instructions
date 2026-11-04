# Player camera prefab: tree and exact values (Cinemachine v2 reference)

Verified in the reference prefab YAML (read-only study). Not observed in Play. Values marked (I) are inferred.

## Hierarchy
```
Player_Camera (layer: player)     scripts: CameraManager, CameraThirdPerson, CameraShaker, CameraFollowPath
 +- CameraMain (tag MainCamera, local pos 0,3,-6)
 |    Camera, AudioListener, CinemachineBrain, URP camera data (Base, stack: overlay camera)
 |    +- Camera_Overlay (inactive)   Camera (overlay, depth only) + URP data; optional nested speed-lines VFX prefab (local z=3)
 +- FreeLook                        CinemachineFreeLook + CinemachineCollider
 |    +- TopRig / MiddleRig / BottomRig   CinemachineVirtualCamera each; child "cm" = Pipeline, Transposer, Composer, BasicMultiChannelPerlin
 +- FollowTransform                 empty; Follow and LookAt target of FreeLook
```
Nesting: `Player_Camera` is nested in the `Player` prefab (override: `_followTarget`, CameraMain position). Variant player prefabs (per game mode) inherit it. Only the overlay camera is in the URP stack; no dedicated UI camera.

## CinemachineBrain
UpdateMethod LateUpdate, BlendUpdateMethod LateUpdate, IgnoreTimeScale off, DefaultBlend EaseInOut 2 s, no custom blends, no events.

## Camera (CameraMain)
FOV 40, near 0.75, far 500, HDR on, MSAA allowed, occlusion culling on, clear flags skybox, depth -1. URP: Base camera, post-processing on, shadows on, antialiasing 0, volume layer mask = one dedicated layer.

## FreeLook (priority 10, standby update 2, CommonLens FOV 40 / near 0.75 / far 500)
- Follow = LookAt = FollowTransform
- BindingMode SimpleFollowWithWorldUp, SplineCurvature 0.2, heading definition velocity, heading filter 4
- Orbits (height, radius): Top (6, 1), Middle (3, 6), Bottom (-1, 3)
- YAxis: value 0.5, range 0..1, no input name, recentering off
- XAxis: -180..180 wrap, MaxSpeed 700, accel/decel 0.1, no input name, recentering off

## Each rig child "cm"
- Transposer: BindingMode SimpleFollowWithWorldUp, FollowOffset (0, 3, -6), XYZ damping 0, angular damping 0
- Composer: ScreenX 0.5, ScreenY Top 0.6 / Middle 0.55 / Bottom 0.5, dead zone 0, soft zone 0.8 x 0.8, lookahead 0, damping 0, CenterOnActivate on
- BasicMultiChannelPerlin: amplitude 0, frequency 0 at rest; noise profile = a Cinemachine package preset (asset identity not resolved: pick any 6D shake preset)

## CinemachineCollider (on FreeLook)
CollideAgainst = default layer + one pathfinding-ignore layer, IgnoreTag Player, AvoidObstacles on, CameraRadius 0.1, MinimumDistanceFromTarget 0.1, Strategy PullCameraForward, MaximumEffort 4, Damping 0, SmoothingTime 0. This is the only occlusion handling; the TransparentLayers mask is 0.

## Overlay camera
CameraType Overlay, clear flags depth only, depth 0, culling mask = one dedicated layer, near 0.3, far 500, shadows and post off, GameObject inactive by default, registered in CameraMain's camera stack. StaticBus events toggle the GameObject.

## Scripts and who drives what
| Concern | Driver |
|---|---|
| FollowTransform | `CameraThirdPerson.LateUpdate`: rotation = target rotation, position = `target.TransformPoint(_followOffset)` with `_followOffset = (0,1,0)`; target set by `CameraManager.Follow(t)` |
| Priorities | not scripted; all vcams priority 10 (I: newest activated wins) |
| State switches | StaticBus events in `CameraManager`: revive and camera-reset (-> `ForceCameraPosition(player.TransformPoint(0,10,-20), rot)` after one `UniTask.Yield`), overlay open/end. Subscribe in Awake, unsubscribe in OnDestroy |
| Vehicle mode | tween FOV 40 -> 60, orbits x1.25, binding -> WorldSpace; reverse on stop; bottom rig from a camera factory (vehicle (-5,3), normal (-5,1)) |
| FOV kick | up to 45 on a trampoline; `SetFOV` writes the lens AND the overlay camera |
| User zoom | scale orbits, max 3x |
| Shake | `CameraShaker` (singleton) sets noise gain on the 3 rigs: `Shake(amp 0.4, freq 3.5, dur 0.2)`, stronger wins, plus decay and lerped variants |
| Flyover | `CameraFollowPath.Follow(points, onStart, onComplete)` |
| Far clip | `CameraFarDistanceZone` trigger per stage (default far 200, deepest zone wins), writes the lens far plane; static list reset on `SubsystemRegistration` |
| Low end | only when the device tier is Low: post-processing off, depth mode none; called from the camera manager `Start` and from a component on extra cameras |

## Reproduce (v2)
1. Install `com.unity.cinemachine` 2.x (the reference pins 2.10.7).
2. Build the prefab per the tree; set the values above; leave axis input names empty.
3. Nest in the player prefab, set `_followTarget`; add manager, shaker, third-person scripts on the root.
4. Wire respawn: reset event -> yield one frame -> `ForceCameraPosition`.
5. Cutscene: disable the FreeLook GameObject, move the Camera along the path, re-enable.
6. Low end: policy switches and per-stage far-clip zones.
