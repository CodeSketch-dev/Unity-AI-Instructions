---
name: ai-navigation-setup
description: "Set up Unity AI Navigation: package check, NavMeshSurface bake, NavMeshAgent, obstacles, links, area costs, agent types, validation. Use when characters or bots must pathfind, an agent will not move, or two areas must connect."
triggers: navmesh, nav mesh, navmeshagent, navmeshsurface, pathfinding, bake navmesh, navmeshlink, navmesh obstacle, agent will not move, path not found, patrol, click to move, tim duong, bot di chuyen, bake duong di
---

# AI Navigation setup

Source: official (Unity-Technologies/skills/initialize-ai-navigation), re-written; [ours] marks additions. For waypoint-based bots without NavMesh see `bot-brain-waypoints`; for jump links see `nav-traversal-link-tool`.

## Steps
0. Package: `com.unity.ai.navigation` must be in `Packages/manifest.json`. Do not invent a version: read the registry or copy the version of an adjacent Unity package; a wrong version fails silently. Ask before adding packages.
1. Inspect what exists (MCP): NavMeshSurface, NavMeshAgent, NavMeshObstacle, NavMeshLink, NavMeshModifier; configured agent types (Window > AI > Navigation). Summarize before changing.
2. Decide: walkable geometry, agent radius/height/step/slope, behaviour (patrol, chase, click-to-move), obstacles, links, area costs.
3. Build in this order: Surface (collect objects by layer/tag, bake), Agent, Obstacle (carving only for rare static-ish blockers; carving moving objects is expensive), Link, Modifier / Modifier Volume (areas), then movement script.
4. [ours] Scene-authored: the Surface lives on a prefab in the scene (see `scene-authored-prefabs`), baked data saved with the scene, never baked at runtime on mobile.

## Troubleshooting (agent will not move)
- NavMesh baked (blue overlay) and the agent stands ON it (`NavMeshAgent.isOnNavMesh`); agent type of Surface and Agent match.
- Destination reachable: `NavMesh.SamplePosition` first, then `SetDestination`; check `pathStatus` and `hasPath`; area mask allows the area.
- Agent `updatePosition`/`updateRotation` not fought by a Rigidbody or root-motion animator.
- Disconnected islands need a NavMeshLink; stairs/ledges need step height, slope, or a link.
- Moving platforms: re-bake is not an option; use links or leave the agent.

## Perf [ours]
Stagger `SetDestination` (not every frame, repath on distance threshold with sqrMagnitude), cap simultaneous agents on low-end Android, disable agents out of range, set avoidance quality to low or none for crowds.

## Validate
Bake succeeds, a test agent reaches a target in Play, Console clean, screenshot of the baked mesh in the Scene view.
