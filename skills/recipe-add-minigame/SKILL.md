---
name: recipe-add-minigame
description: Add a minigame or mode (enum id, scene, selection asset, factory, data, UI entry, verification). Use when a GDD adds a new playable mode or stage type.
---

# Recipe: add a minigame

Traced from knife-tower `Minigame_Type`, `Minigame_Selection_Asset`, `Factory_Minigame`, `Data_Minigame` (report 03, VERIFIED).

1. **Enum** value in `Minigame_Type` with a stable explicit number grouped by family (e.g. 0, 1, 2, 11, 101, 201). The enum is a dictionary key and names are saved in sort order: NEVER renumber or rename. Analytics names (`{type}_...`) are generated from it.
2. **Scene** under `Scenes/` with the master component, player spawn, checkpoints (ascending index), collectibles. If weapons are disallowed, add the type to the project's false-list.
3. **Selection asset** `Configs/Minigame/<Title>.asset`: type, title, load type (transition default; loading screen for heavy init), thumbnail, loading background, coming-soon flag, AI spawn config, scene. `OnValidate` fills the scene name; add the scene to Build Settings (the asset has a button).
4. **Register** in `Factory_Minigame` array; `OnInitialize` builds the map (duplicate -> warning; make it an error in new code). `Get(type)` logs on miss.
5. **Data**: per-type enter/completed `DataValue`s are created lazily. Own persistent domain -> new `Data_<Name>` + `Factory_<Name>` (+ singleton asset, `factory-singleton-template`).
6. **UI**: the selection screen builds entries from the factory list (saved sort order else array order); remote config may reorder with aliases.
7. **Feature layout**: `Event/Minigame/<Name>/`, `Logic/Minigame/<Name>/`, pooled fx under `Configs/Pool/<Name>/` with `PoolPrefabItem` prefabs (`pool-everything`).
8. **Verify** with Unity MCP: entry shows, tap loads the scene, back/home works, no duplicate-type warning, Console clean.

A scene per minigame is the reference convention; defaults, not law.
