---
name: physics-callback-troubleshooting
description: "Diagnose PhysX 3D problems: OnCollisionEnter/OnTriggerEnter not firing, raycast misses, tunneling, ragdoll explosion, gaps, non-uniform scale. Use when a collision, trigger or raycast does not behave. First-match checklist, no guessing."
triggers: oncollisionenter not firing, ontriggerenter not firing, raycast miss, tunneling, kinematic, charactercontroller collision, layer collision matrix, meshcollider convex, ragdoll explodes, physics bug, va cham khong chay, trigger khong chay, xuyen tuong, raycast khong trung
---

# Physics callback troubleshooting (3D)

Source: official (Unity-Technologies/skills/physics-3d-collision), re-written; [ours] marks additions. For our actor/world dispatch pattern see `collision-registry`.

## Method
Walk the list in order and stop at the first confirmed cause. Read the components on BOTH objects first (MCP `gameobject-component-get`, layers, Is Trigger, Rigidbody kind, scale). At most 5 tool calls before you commit to the most likely diagnosis.

## OnCollision* not firing
1. At least one object has a (3D) Rigidbody. Two static colliders never fire.
2. `CharacterController` never gives OnCollisionEnter: use `OnControllerColliderHit`. Do not add a Rigidbody to it.
3. Matrix: dynamic-dynamic yes; dynamic-static yes; dynamic-kinematic yes (dynamic side); kinematic-kinematic, kinematic-static, static-static NO.
4. Layer Collision Matrix allows the pair. Avoid `Physics.IgnoreLayerCollision` for one pair (global, persists across scenes); `Physics.IgnoreCollision` is lost when a collider is destroyed or pooled: re-apply on spawn.
5. Neither collider is a trigger; both enabled and active.
6. The script is on the GameObject that owns the Collider/Rigidbody (the body root, not a random parent).
7. MeshCollider: a non-convex one on a dynamic body is ignored; two non-convex meshes do not collide; inverted normals push objects in.
8. Non-uniform parent scale (for example 1,2,1 or 0.01 import scale) distorts child colliders: bake scale in the DCC tool.
9. A child Rigidbody splits the compound body of its parent.

## OnTrigger* not firing
One side needs a Rigidbody (kinematic is fine) and one collider has Is Trigger. Two kinematic triggers without a dynamic body do not fire in all combinations: test with one Rigidbody non-kinematic.

## Raycasts
Origin inside the target collider misses it; inactive objects and disabled colliders are invisible; triggers are skipped unless `QueryTriggerInteraction.Collide`; check the layer mask and distance. `Time.timeScale = 0` freezes simulation but not raycasts.

## Other
- Tunneling at speed: Continuous / Continuous Dynamic, thicker colliders, or sweep casts; do not shrink fixed timestep first.
- AddForce stops working: body is asleep or kinematic; wake it.
- Ragdoll explodes on frame 1: overlapping bones, joint limits or colliders; disable self-collision between neighbours.
- Gap before touch: default contact offset; check collider size and skin.
- Transform moved by script not yet seen by queries: `Physics.SyncTransforms()` or leave `autoSyncTransforms` off and sync deliberately [ours: keep it off for performance].
- Kinematic bodies: move with `MovePosition`/transform, not `velocity`.

## Verify
Reproduce in a minimal Play test (EditMode cannot step physics), log the pair and the fixed rule, re-run, Console clean. Report which check confirmed the cause.
