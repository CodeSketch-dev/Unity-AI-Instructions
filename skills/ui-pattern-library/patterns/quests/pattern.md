# Pattern: quests

NOT mined from a reference (the projects only have tutorial pointers named `Quest_*`). This contract is a DESIGN (INFERRED) from `recipe-quests-achievements` (report 20); replace positions from the target game's capture. Contract: `spec.yaml`; wireframe `mockups/wireframe.png`.

## Behavior and hooks
- Daily quest rows (3) from `Quest_Asset` (stat, target, reward, period); progress comes from one stat bus (`Stats.Add`, event-driven, no per-quest Update); claim posts the reward flow and marks claimed; all-claimed state shows the next reset time.
- Reroll one quest via rewarded ad (`ads-popup-flow`); resets by UTC day with a clock guard (`recipe-retention-timers`).
- HUD button notify dot when any quest is claimable; toast on completion (`ui-feedback-toasts`). Achievements (tiered, with badges) are a second tab (variant).

## Binding
`Quest_Asset` pool, `Data_Quest` (active, progress, claimed, reset day), stat names shared with the GDD.

## Variants
1. Periods: daily only (default) / daily + weekly tab. 2. Reroll: ad (default) / currency / none. 3. Achievements tab with tier badges.

## Checks
Progress counts exactly once per event; claim twice impossible; reset at the day change; rows keep order after a claim; contract lints; `ui-validator` clean.
