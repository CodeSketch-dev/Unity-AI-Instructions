---
name: clone-feature-recipes
description: "Use when a clone feature needs a reusable behavior/data/config/UI/wiring contract without hard-coded genre-specific balance values."
---

# Clone feature recipes

Common Roblox-clone features have a stable shape. Starting from a recipe skips the design phase, avoids forgotten edge cases and keeps the chain complete (data, config, factory, events, UI, wiring, verification). The recipes are in `references/recipes.md` (read only the recipe you need; the file has a table of contents).

## How to use a recipe
1. Name the feature from the active GDD and find the matching capability recipe. No exact match -> combine the closest two and note the differences.
2. **Check the GDD/evidence first**: `reference-index` may confirm an explicitly selected capability, but neither a recipe nor a reference project is a default design for the clone.
3. Copy the recipe's checklist into the spec/plan, replacing placeholders with observed facts from the GDD and leaving unobserved numeric tuning to `economy-progression-design`.
4. Build following `config-driven-feature`; wire and verify with `done-means-wired`; add the recipe's test scenarios to the QA matrix (`unity-qa-playtest`).
5. After building, add what you learned (a new edge case, a trap) back to the recipe so the next project benefits.

## Recipe format
Each recipe states: player-visible behavior, persistent data, config assets and registry, events, UI, edge cases, performance notes, and how to verify. Keep recipes short; link to skills for the how.
