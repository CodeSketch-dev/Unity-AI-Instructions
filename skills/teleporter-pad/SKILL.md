---
name: teleporter-pad
description: "Teleporter pads and portals: paired or destination mode, fades, anti ping-pong, control-state restore, camera warp. Use when adding portals, zone travel pads or teleports between areas."
---

# Teleporter pad

From knife-tower `Teleporter.cs` (report 04 sec 8.3, VERIFIED; static guard not reset there: INFERRED risk).

- `Teleporter : OptCollisionRegister` + `ICharacterCollidable`; either a paired `_otherTeleporter` or a `_destination` transform.
- Sequence with UniTask: block control (save the character's `ControlState`), fade out 0.2 s, move (position and rotation), fade in 0.2 s, restore control in a `finally` block so an exception never leaves the player frozen. Cancel on destroy (`async-cancellation`).
- Anti ping-pong: a static set of teleporting characters plus a per-instance "waiting for exit" set; the arrival pad ignores the character until it leaves the collider. Reset the static set at `SubsystemRegistration`.
- Camera: after the move call the rig's warp (`OnTargetObjectWarped` / force position next frame) so the camera does not sweep through the level (`freelook-third-person-camera`).
- Bots: teleport only players unless the design says otherwise; a world-list popup can reuse the same service (`world-list` pattern posts `Event_Teleport`).
- Config: fade durations, sfx, optional unlock requirement in a serialized config; no per-callback magic numbers.

Verify in Play Mode: enter, arrive, no immediate return, leave and re-enter works, kill the task mid-fade (disable the object) and control is restored.
