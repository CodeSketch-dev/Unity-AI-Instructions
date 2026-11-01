---
name: recipe-add-pickup
description: Add a collectible (coin, gem, boost) with registry collision, data write, sfx, respawn and prefab. Use when a GDD or request adds a new pickup type.
not: localization, language, translate, ngon ngu
---

# Recipe: add a pickup

Detect the target framework first (`framework-version-map`); its collision/data/audio APIs determine the implementation. Reference evidence may validate a selected capability but must not supply class names, paths, currencies, timers, or prefab defaults.

1. **Runtime behavior**: implement only the GDD-selected interaction, actor eligibility, value/reward rule and optional respawn policy using the target's installed collision API.
2. **Collect-once memory**: add it only when the GDD requires it, through the target persistent-data contract. Generate/store stable instance identity only if authored instances must be remembered.
3. **Effect**: route the configured reward through the target's data/event/audio/UI services; do not name a currency, notification, or audio registry in the recipe.
4. **Wiring**: author the target-defined prefab/scene contract, collision layer and trigger policy. Use the framework registry where installed; never add a parallel callback path.
5. **Lifecycle**: use the project's configured pooling/respawn/cancellation policy; do not assume a tween library or a timer.
6. **Fx**: pool repeatedly spawned presentation through the installed pool.
7. **Verify** (Unity MCP, not file edits): compiles, no console errors, collect as player changes value and HUD, restart shows persistence, respawn works, non-player does not collect.

All concrete pickup behavior comes from the active GDD/evidence; this recipe supplies only the required integration chain.
