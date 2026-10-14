---
name: nav-traversal-link-tool
description: "Editor tool and runtime rules for NavMesh traversal links: two-click authoring with snap, scripted parabola traversal, agent-body sync, ladder links. Use when bots must cross gaps, jumps or ladders that the baked navmesh does not connect."
---

# Nav traversal links

From knife-tower and monkey-escape (report 04 sec 5.4, VERIFIED): `NavTraversalLinkEditor`, `Nav_TraversalLink` (NavMeshLink), `Ladder_NavmeshLink`, `Character_AgentLinkTraversal`.

## Editor window (template: `assets/NavTraversalLinkEditor.cs.txt`, UNCOMPILED)
Two scene clicks create a NavMeshLink between the points: snap each to the ground with a configurable mask (default layers: world and ground layers of the project, not a magic integer), bidirectional toggle, width, container parent object named by purpose, undo support, idempotent by name (re-running does not duplicate), saves the scene dirty flag. Never writes into a project without approval (`rule-editor-tool-safety`).

## Traversal (template: `assets/AgentLinkTraversal.cs.txt`, UNCOMPILED)
- Duration = distance / agent speed. No arc when the link is <= 5 m; otherwise apex = `v^2/2g + 0.01 * distance` (jump speed v, gravity g) with an ease in-out curve.
- The agent's link traversal must be set to Custom (the reference warns otherwise); during traversal clear AI input and block jumps; after landing resume following.
- Sync: overwrite the nav agent body position and velocity from the KCC motor in `LateUpdate` so the agent never fights the controller.
- Ladder links connect the bottom and top of a ladder so bots path onto it (`ladder-climb`).

## Rules
One nav backend per game; rebake the NavMesh and SAVE THE SCENE after moving zones (`mesh-merge-baker`); keep links few (a link per gap, not per platform). Verify in Play Mode that a bot crosses every link in both directions.
