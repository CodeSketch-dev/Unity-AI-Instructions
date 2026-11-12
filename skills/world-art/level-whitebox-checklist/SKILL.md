---
name: level-whitebox-checklist
description: "Whitebox-to-playable checklist for a map or level: player metrics, greybox first, critical path, tension and rest pacing, teach-then-test, gating, guidance, soft-lock check. Use when blocking out or reviewing a level layout, before any decoration."
triggers: whitebox, greybox, blockout, level layout, critical path, pacing, soft lock, dead end, landmark, teach then test, level metrics, map too empty, map confusing, lay out map, bo cuc map, thiet ke man choi, bi lac
---

# Level whitebox checklist

Source: third-party example (practice), rewritten. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/level-design. Complements `zone-level-design` (zone ladder, kits, budgets); this adds the playability gates to pass before dressing.

## Order of work
1. **Metrics first.** Measure the character: run speed, jump height and distance, reach, camera range, dig/tool range. Size every gap, ledge, corridor and doorway in those units; write them in the level doc.
2. **Blockout.** Whole level from untextured primitives at true scale. No art, no decor. Walk it in Play Mode.
3. **Critical path.** Mark start to goal, plus the path most players will take. Optional and secret routes branch off it.
4. **Pace it.** Alternate tension and rest. Put a breather and a safe point before every climax; avoid three of the same encounter in a row.
5. **Teach, then test.** Introduce each mechanic in a safe space, let the player practice, then test under pressure. Difficulty is a sawtooth, not a ramp.
6. **Gate with intent.** Locks, abilities, one-way drops; telegraph irreversible moves.
7. **Guide without walls.** Light, color, leading lines, landmarks visible from decision points.
8. **Playtest cold.** One uncoached player; note where they stop, backtrack or get lost; fix the blockout.
9. **Only then dress** (kits, props, lighting, performance budgets).

## Validation checks
- Reachability: every required point reachable with the baseline abilities.
- Soft-lock: any key/ability needed to pass a gate is obtainable before it; test the key order, not just connectivity.
- Scale: a doorway or ramp the camera cannot frame is a defect.
- Orientation: from spawn, a landmark is visible and the next goal is guessable in 10 s.
- Cost: static geometry plan for combining/culling before decoration (`world-batching-culling`).

## Pitfalls
- Dressing before it plays; geometry ignoring metrics; flat pacing; hazard first met in a lethal spot; irreversible drops with no sign; procedural content standing in for authored pacing.

Related: `zone-level-design`, `intro-camera-flyover`, `prototype-keep-kill`, `checkpoint-respawn`, `world-batching-culling`.
