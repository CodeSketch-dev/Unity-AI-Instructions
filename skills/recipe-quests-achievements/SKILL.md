---
name: recipe-quests-achievements
description: "Stat-driven quests and achievements: one stat bus, quest and achievement assets, daily and weekly resets, red dot. For quests, missions and badges."
---

# Recipe: quests and achievements

- One entry point `Stats.Add(type, amount)` updates `Data_Stats` and posts `Event_Stat_Changed(type, total)`. Gameplay never touches quest objects.
- `Quest_Asset { id, stat, target, reward, period }`, `Achievement_Asset { id, stat, tiers[{target, reward}], badge }`, `Factory_Quest`.
- `Data_Quest`: active daily set, reset day/week, progress, claimed flags. Quest logic subscribes once to the stat event; no per-quest Update.
- Daily set mixes quick, medium and long tasks; rewarded-ad reroll of one quest is optional.
- UI: quest popup (rows with progress and Claim), achievement list with tiers, HUD red dot, completion toast.
- Reset times use UTC day/week and the clock guard in `recipe-retention-timers`.
- The GDD lists stats, the quest pool, targets, rewards and tiers.
