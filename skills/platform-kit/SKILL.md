---
name: platform-kit
description: Reactive platform recipes (trampoline, conveyor, fade, glass bridge, force zone, kill zone, moving platform) built on the collision registry and KCC hooks. Use when building obby/tower platforms.
---

# Platform kit

All reactive platforms derive the framework register + `ICharacterCollidable` (`collision-registry`): no per-platform `OnTriggerEnter` + `GetComponent`. Numbers are the reference defaults (report 04 sec 7, VERIFIED); expose them as serialized config and override per game.

| Platform | Mechanic and defaults |
|---|---|
| Trampoline | on ground hit: mode Multiplier (bounce = fall height x 1.5, min fall 0.5 m, repeat bounce at least 5 m) or ExactHeight 5 m; launch speed `sqrt(2 g h)`; `ForceUnground(0.25)`, velocity applied after 0.05 s, post `Event_Trampoline_Bounced`; press visual 0.2 m / 0.1 s OutQuad then OutBack; random sfx from an array |
| Conveyor | per stable character `AddVelocity(dir * velocity * dt)` with velocity ~700 (impulse added once per frame), optional move boost, against-motion multiplier from config, belt size scales the mesh |
| Fade / countdown | fade out 0.75 s, reappear delay 2 s, fade in 0.75 s; countdown variant 3 s with warning colour red, fade 0.2 s, keep-in 1 s and a text |
| Glass / bridge | breakable pane respawn 2 s; bridge of segment pairs (L/R), one pane safe; segment count 3, spacing 0.1 |
| Breakable | break on touch with a timer; pool fragments (`pool-everything`) |
| Moving platform | KCC `PhysicsMover` + `IMoverController` driven by an animation sequence; action buttons toggle sequences |
| Force zone | constant push speed ~10 along a direction (local up default) |
| Kill zone | trigger -> `Character.Kill(Killer_Type)` (Obstacle, Enemy, Boss, Other, ObstacleBypassImmortal) |

KCC hooks a controller needs: `AddVelocity`, `ForceUnground`, `EnterSinkZone`, `ProcessTrampolineCollision`, swing API (`kcc-advanced-movement`).

## Rules
- Config per platform asset or serialized fields; no magic numbers in the callback bodies; callbacks stay tiny.
- Register all colliders of the object; platforms that toggle must register/unregister in `OnEnable/OnDisable`.
- Reset static collections at `SubsystemRegistration`; stop tweens in `OnDestroy`.
- Gap and height budgets from `roblox-world-kit` (<= 0.8 x computed jump distance, rise <= 1 stud).
- Verify each platform in Play Mode via Unity MCP (step on, jump off, die and respawn on it, 2 characters at once) before reporting done (`done-means-wired`).

Related: `ladder-climb`, `checkpoint-respawn`, `teleporter-pad`, `zone-level-design`.
