---
name: roguelite-run-loop
description: "Design a roguelite run loop for a mobile game: short run, seeded generation, risk and reward choices, permadeath with meta progression, loot tables, run summary. Use when adding a run-based mode, endless dive or procedurally varied levels."
triggers: roguelite, roguelike, run based, endless run, procedural level, seed, meta progression, permadeath, run summary, random rooms, che do chay, ngau nhien, mo hinh run
---

# Roguelite run loop

Source: third-party example (genre ideas), rewritten and reduced to what fits mobile. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/genres/roguelike and skills/disciplines/procedural-gen. Not a grid-turn dungeon template.

## Loop
1. **Run** (2-6 min): start with a loadout from meta progress, move through generated segments, make 1-2 risk/reward choices per segment, end by death, exit or goal.
2. **Summary:** show what was earned, one clear next upgrade, and a prominent retry button. Rewarded-ad doubling belongs here, not mid-run.
3. **Meta:** permanent upgrades bought with run currency; every run should move the player at least one step.

## Generation rules
- Use a seeded RNG per run (store the seed in the run state); one RNG instance per system so adding a roll does not reshuffle another system.
- Generate from hand-authored chunks with connectors, not pure noise; validate reachability and a minimum reward density after generation.
- Difficulty by chunk index with a sawtooth (hard chunk, breather, hard chunk). Never two unwinnable rolls in a row; add pity for rare drops.
- Loot: weighted tables with displayed odds equal to real odds (`loot-rarity-tables`).

## Mobile constraints
- Persist only run seed + progress checkpoints, never scene objects; a resumed app must not lose the run (`save-and-crash-safety`).
- Pool spawned chunks and enemies; stream chunks ahead of the player.
- One-handed, readable at a glance; no menus mid-run beyond a choice popup.

## Verify
Simulate 1,000 seeds headless for reachability and reward variance; play 3 seeds by hand; confirm no soft-lock and acceptable run length.

## Pitfalls
- Randomness without agency (the player cannot influence outcomes).
- Meta upgrades that trivialize early runs.
- Death with no reward, so retry feels punishing.

Related: `loot-rarity-tables`, `simulator-pacing-checks`, `level-whitebox-checklist`, `npc-bots-and-enemies`, `pool-everything`.
