---
name: game-clone-recon
description: "Start-of-clone recon: feature inventory, system breakdown, reference map, fidelity labels, staged build order before any code. Use on \"clone game X\", \"make a game like X\", or shared reference screenshots/videos."
---

# Game clone recon

Cloning goes wrong when work starts from memory of the game instead of from evidence. This skill front-loads the evidence so every later task can say "match reference X" and mean something checkable.

## Steps

0. **Use existing analysis.** If `docs/gameplay-analysis.md` exists (from `gameplay-video-analysis`), build on it; otherwise run that skill first when the user supplied videos or play notes. Classify the genre with `roblox-genre-patterns`. The whole pipeline is mapped in `clone-pipeline`.
1. **Collect references.** Ask for, or locate: screenshots/video of the target game, existing Unity projects that already implement similar mechanics (internal or open), asset packs. Treat reference projects as read-only. Record absolute paths in `docs/reference-map.md`.
2. **Inventory features** as a flat table: feature, player-visible behavior, where it appears in the reference (screenshot/file), priority (core loop / retention / polish). Describe behavior as observable facts ("boss chases only while the player carries a pet"), not implementation guesses.
3. **Find the core loop** in one sentence (e.g. break egg -> get pet -> carry to base -> income -> upgrade). Everything not serving the loop is a later stage.
4. **Match recurring features to recipes** in `clone-feature-recipes` and look up each in the reference with `reference-index`; only novel features need fresh design.
4b. **Break into systems** (character/input, world/zones, economy, progression, enemies/AI, bots/other-players, UI/HUD, shops, FX/audio, persistence, monetization hooks). For each, note which reference project already contains a similar implementation; reuse beats reinvention.
5. **Choose fidelity per system**: `exact` (UI layout, placement, numbers), `faithful` (same behavior, own art), `free` (own design). Ask the user only where the choice is genuinely theirs; default to `exact` for anything the user supplied screenshots of.
6. **Stage the build**: playable core loop first (greybox is fine), then economy/progression, then content breadth, then polish/FX, then perf pass. Each stage ends with something playable.
7. **Write the output** to `docs/clone-plan.md`: loop, system table with fidelity + reference path, staged order, open questions, risks (licensing of ripped assets, missing source scripts).

## Why this order
Fidelity labels prevent two common failures: over-matching things the user doesn't care about, and under-matching things they will scrutinize screenshot by screenshot.

## Output rules
Keep the plan short enough to re-read at the start of every session. Update it as stages complete instead of creating new plan files.
