---
name: recipe-add-minigame
description: Add a minigame or mode (enum id, scene, selection asset, factory, data, UI entry, verification). Use when a GDD adds a new playable mode or stage type.
not: localization, language, translate, ngon ngu
---

# Recipe: add a minigame

Reference evidence may inform a target's installed mode API, but it must not supply registry names, IDs, paths, scenes, or gameplay defaults. Resolve every such value from the active GDD and target framework profile.

1. **Identifier**: use the target's GDD-selected, persisted mode identifier. Preserve existing serialized IDs; do not invent a numbering scheme or rename a saved identifier.
2. **Scene**: create only the GDD-selected scene/content contract and register it through the target's scene-loading flow.
3. **Selection data**: use the target's configured registry/asset location and only fields the GDD defines. Add required scenes through the target's Build Settings workflow.
4. **Register** in the target's installed mode registry. Build/cache lookups in its normal initialization hook, reject duplicate IDs, and handle misses through the project policy.
5. **Data**: persist only GDD-selected per-mode state using the target data/factory pattern.
6. **UI**: build entries from the configured registry only when the GDD includes mode selection.
7. **Feature layout**: derive folders, pool location and prefab contract from the target project profile; do not impose a mode-specific path.
8. **Verify** with Unity MCP: entry shows, tap loads the scene, back/home works, no duplicate-type warning, Console clean.

A scene per mode is a target-specific decision, never a recipe default.
