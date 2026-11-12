---
name: scene-naming-conventions
description: Scene, prefab and asset naming conventions and folders for a clone project, checked by the naming lint. Use when creating scenes, prefabs or assets.
---

# Scene and asset naming

- Scenes in `Assets/_Game/Scenes`: `Boot`, `Home`, then `Game_<Mode>`; build index 0 is the boot scene.
- Prefabs in `Assets/_Game/Prefabs/<Feature>/`, named `<Feature>_<Part>`; UI names follow `ui-naming-conventions`.
- Config assets in `Configs/<Feature>/` named by id; factory singleton naming per the installed framework (`factory-singleton-template`).
- No spaces, no leading digits, no duplicate names across features.
- Keep established spellings in an existing project; do not rename legacy folders to normalize.
