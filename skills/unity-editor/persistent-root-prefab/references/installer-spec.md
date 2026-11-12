# Installer spec (what FoundationInstaller must do; idempotent, no hand-written YAML)

Implemented as an Editor script in `new-game-bootstrap/assets/FoundationInstaller.cs.txt`. Menu: Tools/Foundation/Install Persistent Root.
1. Ensure `GameSingleton.cs` exists (writes the small class if the project has none). Wait for compile before building the prefab (run the menu twice, or call it from `[DidReloadScripts]`).
2. Build `Assets/_Game/Prefabs/GameSingleton.prefab` in memory: `EventSystem` (+ input module chosen by installed packages), `Manager` (+ `Pool`, `IAP` empty children, frame-rate component if the package has one), `Canvas` / `Canvas_Popup` / `Transition` with the canvas table values, `Root` stretch children, `SafeArea`, `ViewContainer`, `PopupRoot`, `OverlayContainer`, `LoadingScene` shell, `Ads_NativeSlot` shell.
3. Attach framework components by type name when the type exists (`UISafeArea`, `PopupRootSetter`, `ViewContainer`, `FpsUnlock`); log what was skipped. Never add a component that cannot be resolved.
4. Save with `PrefabUtility.SaveAsPrefabAsset`; if the file exists, add only missing children (never delete user work).
5. Place the instance in the open scene if none exists (`PrefabUtility.InstantiatePrefab`), report other EventSystems (delete only the empty scene ones), mark the scene dirty.
6. Print a report: created, skipped, sort orders read back from the saved prefab.
Not done by the installer: the loading screen script, internet monitor, transition asset (project or vendor specific), SDK components, HUD content.
