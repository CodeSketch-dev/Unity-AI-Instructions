---
name: clone-feature-recipes
description: Checklists for recurring Roblox-clone features (eggs/hatching, pets, treadmill, zones/gates, shops, upgrades, rebirth, daily reward, index, bots, rewarded boosts). Use when adding any such feature or listing a clone's systems.
---

# Clone feature recipes

Common Roblox-clone features have a stable shape. Starting from a recipe skips the design phase, avoids forgotten edge cases and keeps the chain complete (data, config, factory, events, UI, wiring, verification). The recipes are in `references/recipes.md` (read only the recipe you need; the file has a table of contents).

## How to use a recipe
1. Name the feature and find its recipe. No exact match -> combine the closest two and note the differences.
2. **Check the reference first**: `reference-index` query for the feature in the reference projects; the recipe is the default, the reference wins where they differ (fidelity label from `game-clone-recon`).
3. Copy the recipe's checklist into the spec/plan (`spec-then-plan`), replacing placeholders with real names and numbers (`economy-progression-design` for the numbers).
4. Build following `config-driven-feature`; wire and verify with `done-means-wired`; add the recipe's test scenarios to the QA matrix (`unity-qa-playtest`).
5. After building, add what you learned (a new edge case, a trap) back to the recipe so the next project benefits.

## Recipe format
Each recipe states: player-visible behavior, persistent data, config assets and registry, events, UI, edge cases, performance notes, and how to verify. Keep recipes short; link to skills for the how.
