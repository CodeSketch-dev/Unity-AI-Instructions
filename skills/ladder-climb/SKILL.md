---
name: ladder-climb
description: "Ladder climbing for the KCC character: ladder collider and cache, BoxCast probe, enter/middle/exit states, jump-off and a bot nav link. Use when a map needs ladders or vertical climbs."
---

# Ladder climb

From knife-tower `Ladder.cs` and `CharacterKC` (report 04 sec 8.1, VERIFIED).

- `Ladder : MonoCached` with a BoxCollider, `_height`, optional tiled model (`_modelHeight`). A static `Dictionary<Collider, Ladder>` cache and a `Collider.IsLadder(out Ladder)` extension avoid `GetComponent`; reset the static cache at `SubsystemRegistration` (the reference does not).
- Detection in the controller, only with move input: BoxCast 0.2 cube, 0.35 up, reach `radius + 0.1`, every 0.05 s.
- States `ClimbingLadder` with sub-states Enter / Middle / Exit: Enter lerps to the ladder surface at padding 0.2 (lerp speed 100), Middle climbs `input.z * climbSpeed` (5 m/s; 7.5 in the obby profile), Exit over the top (`y > Height`) lerps forward by padding + 0.1.
- Jump input detaches backwards at `-StableMoveSpeedMax`; gravity and grounding are suspended while climbing; bots never jump while climbing.
- Bots: a `Ladder_NavmeshLink` lets the nav agent path onto ladders (`nav-traversal-link-tool`, `bot-brain-waypoints`); ladder detection ahead 0.8 m.
- Animator: `IsClimbing`, `ClimbY`; keep the hash guards (`kcc-character-controller`).

Verify: climb up and down, jump off, reach the top edge, bot climbs, respawn while on a ladder resets the state.
