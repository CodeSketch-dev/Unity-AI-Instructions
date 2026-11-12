---
name: consistency-check
description: "Cross-check shared values and names across design docs, code, configs and tests: constants, prices, rates, ids, labels. Use after balance or rename changes, before release, or when numbers in docs disagree with the game."
triggers: consistency check, doc code mismatch, constants mismatch, price mismatch, naming consistency, config drift, khong dong nhat, lech so lieu, sai gia, kiem tra nhat quan
---

# Consistency check

Use when one value lives in several places and could drift.

## Steps
1. Pick the facts to audit: economy numbers (prices, rewards, rates, timers), caps and limits, ids/keys, player-visible names and terms, tuning constants.
2. For each fact find every place it appears: design doc, config assets, code constants, tests, localization, store/IAP lists. Use code search first (code graph or grep), then Unity MCP for ScriptableObject and prefab values (a file grep cannot see serialized values reliably).
3. Build a table: fact | source of truth | other copies | match? Declare the source of truth (usually the config asset or one named constant); the rest must derive from it.
4. Fix mismatches at the source of truth, then regenerate or edit copies. Replace duplicated literals with a reference where cheap.
5. Terminology: one player-visible name per concept; check UI strings, toasts and tooltips together.
6. Re-run tests that encode the numbers; update tests only when the source of truth changed on purpose.

## Checklist
- No literal duplicates left for money, odds or time values.
- Docs updated in the same change as numbers.
- Localization keys exist for every visible string touched.
- Save-data ids and IAP ids were NOT renamed (rename only the visible text).

## Output
Facts audited, mismatches found, which were fixed, which remain and why.
