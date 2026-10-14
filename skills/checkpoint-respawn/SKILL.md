---
name: checkpoint-respawn
description: "Checkpoints, fall detection and the revive loop: ICheckpoint, manager and static queries, saved progress, respawn delay, camera reset. Use when adding checkpoints, kill zones, falling death or respawn to an obby or tower."
---

# Checkpoint and respawn loop

From knife-tower and monkey-escape `Checkpoint/*`, `CharacterFallDetector`, `Character_Dead` (report 04 sec 3.4, 8.2, VERIFIED).

## Pieces
- `ICheckpoint {Index, Transform}`; `Checkpoint : OptCollisionRegister` posts `Event_Checkpoint_Enter`; for the player only, when `_index > Data_Checkpoint.Value` it saves and plays fx, sfx and haptic (`Taptic.Success`).
- `Checkpoint_Manager : MonoSingleton` holds the array; `Checkpoint_Static` queries: player, next, previous, around-player(range), nearest, with `GetMode.Clamp|Loop` and a `CheckpointCount` DataValue.
- `Character_Checkpoint.Now` (DataValue) tracks every actor's index (bots too).
- `CharacterFallDetector.Tick`: reset the ground Y while stable or climbing; if `groundY - y > threshold (20)` call `Character.Kill()` (optional ground-raycast veto; NPC threshold 5).
- Revive after `Factory_Character.ReviveDelay` (2 s): place position and rotation at the checkpoint, restore the skin (ragdoll swap only for the player), post `Event_Camera_Reset`.
- Scene authoring: ascending `_index`, a `[Button] SnapToGround`; checkpoints are scene objects, tuning (fx, delay) in a factory (`recipe-add-pickup` patterns for data and events).

## Rules
- Save only on a higher index; bots do not write player progress; the player check uses `IsPlayer`.
- `Checkpoint` posts the event for every character but writes data only for the player.
- Rubber-band bots by checkpoint index distance (`bot-brain-waypoints`).
- Revive consistently resets state: input, velocity, effects, state machine (`kcc-character-controller`).
- ME variants: `Character_Checkpoint_Escape/_Obby`, `Minigame_Checkpoint_Provider` per mode.

Verify in Play Mode: touch checkpoint 2 then fall, respawn at 2 after 2 s, restart the game keeps 2, bots respawn, camera resets. Not Editor-verified here.
