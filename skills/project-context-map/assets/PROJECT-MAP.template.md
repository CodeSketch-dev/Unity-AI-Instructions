# <Game> project map

Updated: YYYY-MM-DD. Unity <version>, <render pipeline>, targets Android/iOS. Framework: <names>. Keep under ~150 lines.

## Run it
- Open scene: `<path>` (boot) -> `<path>` (gameplay). Editor-only: `Application.runInBackground = true`.
- Fast testing: cheat menu (backtick / 3-finger tap), test scene `<path>`, reset save via `<menu or path>`.
- MCP: server `<name>`; Editor must not be in Play Mode when editing.

## Folders
- `Assets/_Game/Scripts/Logic/<Feature>/` runtime; `.../Editor/` tools; `.../Data/` persistent; `.../Factory/` registries; `.../Event/` bus events.
- Configs `Assets/_Game/Configs/<Feature>/`; singleton assets `<path>`; prefabs `Assets/_Game/Prefabs/<Feature>/`.

## Systems
| System | Owner class | Files | Prefab/Scene | Config / Factory | Events |
|---|---|---|---|---|---|

## Data (persistent)
| Record | Fields that matter | Notes |
|---|---|---|

## Editor tools
| Menu path | What it generates | Idempotent? | Re-run when |
|---|---|---|---|

## Reference mapping
| Feature | Reference project path | Fidelity (exact/faithful/free) |
|---|---|---|

## Conventions
- Naming, namespaces, lifecycle rules actually used here (differences from the global house style).

## Gotchas
- <thing that cost time> -> <what to do>

## Current state
- In progress: <task> (spec/plan: <path>)
- Queue: 1) ... 2) ...
- Open bugs: ...
- Last verified: <what ran in Play Mode, when>
