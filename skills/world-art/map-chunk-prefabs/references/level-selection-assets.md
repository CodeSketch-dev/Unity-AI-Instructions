# Level and minigame selection assets

- Selection asset (`SerializedScriptableObject` or plain SO): type enum, title key, thumbnail, scene name (string filled in `OnValidate` from an Editor-only scene asset reference), load type (`Transition` or `LoadingScreen`), optional AI spawn config, and an Editor button "Add to Build Settings".
- Registry: a `Factory_<Game>` singleton asset lists the selection assets. Home has a selection prefab that spawns one item prefab per asset into a ScrollRect (`ui-page-item-prefab`).
- Switching: `Switch()` resets static game state, resolves the scene name (e.g. last visited world from a Data value), then calls the heavy loader or the light loader (`scene-flow-loading`).
- In the target scene a `<Game>_Master` sets the static game type in `Awake` and a GUI loader pushes the HUD view (by prefab reference or addressable reference) with a cancel token cancelled in `OnDestroy`.
- Levels are NOT addressable and NOT loaded by path: the scene is the level; chunks are placed in it. Addressables may serve HUD views and localization tables.
See also `minigame-registration`.
