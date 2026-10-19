---
name: recipe-quests-achievements
description: "Stat-driven quests and achievements: one stat bus, quest and achievement assets, daily and weekly resets, red dot. For quests, missions and badges."
---

# Recipe: quests and achievements

- Route gameplay progress through one target-defined stat/progress service; gameplay never mutates quest objects directly.
- Use target-defined config, registry and persistent progress records with stable IDs and GDD-selected targets, rewards and periods.
- Subscribe once to the target progress event; no per-entry `Update` polling.
- The GDD decides cadence, optional rerolls, reward channels and presentation.
- Use only GDD-enabled UI/notification surfaces.
- Reset/time policy uses the target's UTC/clock-safety contract when periodic content is enabled (`recipe-retention-timers`).
