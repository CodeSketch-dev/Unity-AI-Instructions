---
name: char-animator-reference-parity
description: "Make a ported character animate exactly like the reference when bone names differ: keep the reference controller, retarget clips, port its parameter driver, verify with a play-mode state probe. Use when animation breaks after a rig swap."
---

# Animator reference parity

Why: a hand-built 'simplified' controller looks close but never matches the original's transitions, durations and layers. The reference's behaviour lives in a pair: the controller (plus its overrides) AND the script that drives its parameters. Port both, never one.

## Steps
1. **Find the pair in the reference project**: controller + override controllers, and the script that writes the parameters (grep the parameter-name constants, SetBool, SetTrigger, SetInteger). Read the reference getters: parameter names lie. Example from a real port: 'IsJumping' meant 'jumping AND going up', 'JumpActive' meant 'jumping for the whole airtime', and the hover/fall state only fired when 'JumpActive' was FALSE (falls without a jump).
2. **Dump both controllers through the AnimatorController API** (parameters, layers, masks, states, sub-state-machines, every transition with conditions, exit time, duration, interruption). Diff them. Do not read controller YAML by eye.
3. **Different bone names mean retarget the CLIPS** (curve paths), not the controller. Keep the reference override controllers' clip-to-clip mapping so every state keeps its original timing and speed.
4. **Avatar masks hold bone paths.** A mask authored for another skeleton silently masks nothing (the layer looks dead). Rebuild each mask on the new rig's paths (spine chain maps to the single upper-torso bone, arm chain maps one to one).
5. **Never edit a shared reference asset in place.** Copy the controller into the project, assign the new masks on the copy, create a new override on the copy, and point the SOURCE prefab at that override (not a scene override).
6. **Port the driver with one writer per parameter.** Put a small MonoBehaviour next to the character controller that writes the reference parameters from the character's real state. Guard every write with a cached parameter-hash set that is rebuilt when the controller reference changes (controllers get swapped at runtime for carrying, training, emotes). Give the old driver a flag so it stops writing the parameters the new one owns; default off so other games sharing it do not change.
7. **Write in Update with an execution order after the input system.** LateUpdate writes are applied a frame late and lose to physics-time writers.
8. **Verify in Play Mode with a probe** (see below), not by reading the graph.

## Play-mode probe (the proof)
A temporary MonoBehaviour that feeds scripted input (run, jump, stop) and logs every state change as `time state->next | key parameters`. Compare the logged sequence with the reference graph transition by transition. Pitfall: the probe must run AFTER the game's own input component and BEFORE the driver (execution order), otherwise the driver reads last frame's input and the log shows a false failure. Destroy the probe and restore timeScale afterwards.

## Notes
- A clip of length 0 is a single static pose, normal for a reference Idle (check the original clip's stop time before 'fixing' it).
- A reference prefab may force 'always sprinting'; check its serialized value so Walk vs Run matches.
- Heavy asset edits: stop Play Mode first, save, refresh, read the Console for new errors, then read back the prefab and the scene instance.
(VERIFIED in one Unity MCP session; defaults, not hard rules.)
