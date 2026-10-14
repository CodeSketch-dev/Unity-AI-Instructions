---
name: bot-brain-waypoints
description: "Bots that run an obby course: same character with an AI driver, class states, waypoint graph with grid lookup, 3-ray jump avoidance, stuck checks, rubber-band teleport, one-per-frame spawn, and a waypoint graph checker. Use when adding bot racers or chasers."
---

# Bot brain (waypoints)

Extends `npc-bots-and-enemies` (population, tiers) with the movement brain from knife-tower and monkey-escape (report 04 sec 5, VERIFIED).

## Same character, different driver
Bots use the player's character prefab (type Npc). `AI : MonoCachedFast` writes the same input struct in `Update` (`CharacterKCInputAI {MoveVector, LookVector, Jump}`) and calls `SetInputs(ref)`; clear the input while a nav link is being traversed; an external-move override exists for scripted moves (`kcc-character-controller`).

## Structure
- `AI_State` enum + `IStateMachine` state classes (ME: Stop, Idle, Chase; KT adds many mode states registered per mode) (`state-machine-template`). Chase: `JumpIfNecessary(); if (MoveToGoal(usePathfinding)) OnComplete?.Invoke();` and `AI_Follow_Waypoint` advances on `OnComplete`.
- Components as siblings: Avoidance, Follow_Waypoint, Attack, Battle, Renderer; `AI_Manager` spawns.
- Waypoint graph: `AI_Waypoint` (`next[]`, type Normal / WaitForDistance / Morph, cell x,z, reach radius, `IsReachedExpanded(pos, speed, 0.5)`); `AI_Waypoint_Manager` spatial grid cell 15 m, max upward height delta 7.5, height priority weight 6, nearest-waypoint lookup.
- Follow rules: advance when reached; optional crossing-advance and speed-expanded reach for fast modes; stuck check every 5 s rewinds or teleports; ME config: pathfinding on, velocity-reached on, level randomised per revive.
- Jump heuristics (3 cached NonAlloc raycasts in local space): block (0,0.1,0)->(0,1,1), fall (0,0.5,0.4)->(0,-0.5,0.4), kill (0,0.1,0)->(0,0.1,1); `Jump = obstacleAhead || fallAhead || obstacleKill`; never jump while climbing.
- Rubber band: when a bot's checkpoint index differs from the player's by more than 5 (`TeleportIfFartherThan`), revive it at a checkpoint around the player (range 3) (`checkpoint-respawn`).
- Aggression (battle modes): attack-player probability 0.25, ranged weapon chance 0.15, per-minigame overrides in a factory.
- Spawning: one bot per frame, count scaled by device tier (`device-tier-policy`), registered as a loading task. Bots get random skins, names and auras/trails (`bots-as-players`, `cosmetic-slot-providers`).
- Pathing: the nav agent body is overwritten from the KCC motor every LateUpdate; use one backend (NavMesh agent or the A* package), not both (`nav-traversal-link-tool`). DOTS crowd backends only for >100 chasers (`no-ecs-by-default`).

## Check
Verify in Play Mode via Unity MCP: bots complete the course unaided, recover when stuck, respawn near the player when far behind, and do not allocate per frame.
