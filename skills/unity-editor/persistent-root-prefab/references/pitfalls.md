# Pitfalls

- A transition loader calling `DontDestroyOnLoad` on a non-root child does nothing; it survives only because the parent is persistent. Keep one owner of persistence: the root.
- Children flagged `PersistAcrossScenes = false` while living under the root look wrong but are fine; do not "fix" them by adding more roots.
- Layer drift: UI children sit on layer 5 in some prefabs and layer 0 in others; pick one (UI) when authoring and do not mix.
- The boot scene may carry its own EventSystem from a template: delete it, the root has the only one (two EventSystems warn and fight for input).
- Boot/splash canvases from a vendor SDK may use a different reference resolution; keep them separate from the three game canvases.
- Safe area on `PopupRoot` would shrink popups and dimmers: leave it full-bleed; individual popups may add their own `UISafeArea` child.
- Native-ad slot lists must be static lists (duplicate roots exist briefly), never a single instance field.
- Do not give the root a camera, listener or BGM: the Cinemachine brain, listener and music belong to the scene or the player prefab.
- A lean project does not need a copy in every scene; copies are a convenience for Play-from-any-scene and each is a duplicate-Awake hazard.
- Never build the canvases or the loading hierarchy at runtime to "fix" a missing child; fix the prefab.
- Do not copy two framework copies into one project (a vendored folder plus the package); the prefab must reference the package types.
