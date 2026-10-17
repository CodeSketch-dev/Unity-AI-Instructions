# Play Mode driver gotchas (load on demand)

- Game View size: select by INDEX from the CURRENT group (`GameViewSizes.currentGroupType`, usually Android, not Standalone); size lands one call later: verify `Screen.width > Screen.height` right before each capture.
- script-execute: set class `Script` / method `Main` explicitly; classes it compiles can queue steps on `EditorApplication.update`, but every hook must try/catch and unhook on exception or Play exit (a throwing hook stalls the MCP link until a domain reload).
- MonoBehaviours used by script-execute must live in the runtime assembly (`#if UNITY_EDITOR`), not an Editor folder.
- Never edit scripts while Play runs: compile stalls. Exit Play, refresh, restore data, re-enter; the new code is only live after a fresh Play.
- After entering Play the MCP link may be down for minutes; poll the Editor window title with a Monitor loop instead of resending.
- Restore the dev save only after Play fully stopped (`IsPlaying=false`); copy over, never delete. Writing DataValues in Edit mode also persists: restore then too.
- Popups: `Close()` is ignored while the open tween plays; wait ~8 s before the first tap, owners must retry Close. Claim blocking popups (offline income, free cash) with a real tap before screenshots; isolate each popup shot (snapshot popup-root children, destroy only new ones).
- Context buttons change meaning per state (Steal/Place/Hatch/Drop): tap once, re-read state before the next tap. Tutorial gates hide HUD with CanvasGroup alpha 0: complete the tutorial in Play first.
- Overlay modals built in code must out-sort every game overlay: use `sortingOrder = short.MaxValue`, then screenshot to confirm it is above the open popup.
- Prefab edits through `LoadPrefabContents` + `SaveAsPrefabAsset` can rewrite unrelated serialized values (anchors of scrollbar handles): diff the prefab afterwards or change plain values as text.
- Do not trust Editor per-frame GC: compare p50 across scenarios and time phases with begin/end PlayerLoop probes.
- Frames: an `EditorApplication.update` recorder (ScreenCapture every 0.3 s) tiled with PIL; always OpenScene explicitly and check the active scene name.
