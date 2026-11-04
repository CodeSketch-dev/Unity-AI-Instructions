# Verification

Static (Edit Mode, MCP script):
- Prefab exists once; open it and list canvases: three, sort 2506 / 12506 / 20000, scaler 1920x1080 Expand match 0.
- `GetComponentsInChildren<Camera>/AudioListener/AudioSource` count = 0.
- Missing scripts on the prefab and on every scene holding it = 0 (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount`).
- Exactly one EventSystem across the prefab plus each scene's own roots.

Play (back up the save first):
1. Start from the boot scene: wait for Home. Assert `FindObjectsByType<GameSingleton>` = 1 and `FindObjectsByType<EventSystem>` = 1.
2. `PopupManager` root is non-null; open and close a popup; it appears under `PopupRoot`.
3. Enter a minigame through the loader, return Home, repeat 5 times: object count stable, Console empty (`scene-teardown-safety`).
4. Start Play directly from a gameplay scene that holds a copy: exactly one root survives and the scene plays.
5. Screenshot at 1920x1080: HUD under popups, transition over everything.
Report the counts read back, not "looks fine".
