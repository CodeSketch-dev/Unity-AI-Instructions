# Scene trees (text) of the studio's standard scene types

Home (UI-only hub):
```
Main Camera
Directional Light
GameSingleton [P]                 persistent root (see persistent-root-prefab)
Canvas > Root/SafeArea > { Buttons [P]..., MinigameSelection (spawns item prefabs), Settings button [P], CurrencyBar [P] }
BGM
```
Minigame world (chunks):
```
Directional Light
GameSingleton [P]
Player [P]                        one prefab with nested GUI + camera + character; mode players are variants
<Game>_Master [P]                 master + GUI loader + Optimizer child
Stage (plain container + manager)
  Stage_0 .. Stage_N [P]          chunk prefabs
Shops / Treadmills / Props [P]
```
Tower (floors):
```
Directional Light, BGM, GameSingleton [P], Player [P]
Tower_Manager (plain container + manager) > Floor_1 .. Floor_N [P]
<Game>_Master [P]
```
Rules: scene roots mix prefab instances (player, managers, chunks, root) and plain containers or one-off glue (light, BGM starter, containers); keep roots <= 20; no tool-marker roots; the camera lives inside the player prefab (Home has its own plain camera); there is no environment or skybox root prefab unless the project defines one.
Anti-example: a 241-plain-object hand-built tower inside one 12 MB scene file is the opposite of the chunk rule.
