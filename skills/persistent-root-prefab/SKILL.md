---
name: persistent-root-prefab
description: "Use when creating or fixing the persistent root prefab placed in every scene: EventSystem, HUD and popup canvases, safe area, loading screen, transition, pool, IAP, managers, duplicate self-destroy, sort orders, boot order. Includes install steps and verification."
triggers: game singleton, persistent root, dontdestroyonload, canvas popup, event system, loading screen, popup root, safe area, sort order, boot, global canvas, goc ung dung, canvas toan cuc, dung chung moi scene, kt style, knife tower
---

# Persistent root prefab (GameSingleton)

ONE prefab holds everything that must survive scene loads: EventSystem, the overlay canvases, loading and transition, pool, IAP and global managers. It is authored in Prefab Mode, placed in the boot scene (and in any scene meant to be played alone), and never created from code. Rubric: S01, S02, U05.

## 1. Contents (exact tree: [hierarchy-tree.md](references/hierarchy-tree.md))
Root `GameSingleton` carries ONE script: `GameSingleton : MonoSingleton<GameSingleton>` with `PersistAcrossScenes => true` and no logic. Children, in this order:
1. `EventSystem`: `EventSystem` + the input module of the installed input stack (`InputSystemUIInputModule` for the Input System package, else `StandaloneInputModule`).
2. `Manager`: frame-rate unlock (60, vSync 0), the central game ticker, `Pool` child (prewarm from the pool config factory), `IAP` child, game-wide singletons, global FX and guide prefabs as nested prefabs.
3. `Canvas` (HUD / always-on overlays), `Canvas_Popup` (views, popups, loading, internet, native slot), `Transition` (fade canvas, nested prefab).
No Camera, AudioListener, AudioSource or mixer inside: camera and BGM stay in each scene; audio is created lazily by the framework audio manager.

## 2. Canvases (values: [canvas-table.md](references/canvas-table.md))
| Canvas | Sort | Holds |
|---|---|---|
| `Canvas` HUD | 2506 | `Root/{OverlayColor, CutSceneFocus, SafeArea (HUD prefab), Notification_Warning}` |
| `Canvas_Popup` | 12506 | `Root/{ViewContainer (+safe area), PopupRoot (+PopupRootSetter)}`, `OverlayContainer`, `LoadingScene`, internet popup, native slot |
| `Transition` | 20000 | one full-screen RawImage for the fade |

All: Screen Space Overlay (no camera reference, so scene swaps never break them), CanvasScaler ScaleWithScreenSize 1920x1080 (landscape), Expand, match 0, GraphicRaycaster. Order rule: HUD < popup < transition < debug overlay. Per-mode HUD canvases of a minigame sit below the persistent HUD. `PopupRoot` is not safe-area adjusted.

## 3. Duplicate handling and placement
- The root is placed in the boot scene and in every scene that will be Played alone in the Editor. The second copy runs `MonoSingleton.Awake`, sees an existing instance and destroys its whole GameObject.
- Hazard: code after `base.Awake()` in derived components still runs once in the doomed copy. Guard it (`if (Instance != this) return;`) or keep derived `Awake` bodies idempotent, and unsubscribe in `OnDestroy`. Use static slot lists, not single instance fields, for things like the native-ad slot.
- A lean build needs only the boot-scene copy.

## 4. Reaching it from other code
Nobody calls `GameSingleton.Instance.X`. Children expose static facades (`LoadingScreen.Load`, `PopupManager.Create`, `UIGlobalCanvas.Canvas`) and talk through `StaticBus` events (`static-bus-events`). Child managers inherit `MonoSingleton<T>` for their own static `Instance`; their `PersistAcrossScenes` flag is misleading under a persistent parent, behavior is decided by the root.

## 5. Boot order (details: [boot-order.md](references/boot-order.md))
`SubsystemRegistration` static resets -> boot scene Awake (singletons first, execution order -50) -> `AfterSceneLoad` init class (frame rate, device policy, settings binding) -> save warmup -> load Home. Heavy scene loads go through the loading screen, light ones through the transition loader (`scene-flow-loading`). Init owners: `boot-sequence-setup`.

## 6. Build it (step by step)
1. Run the Editor installer from `new-game-bootstrap` (`FoundationInstaller`) for the skeleton, or follow [installer-spec.md](references/installer-spec.md) by hand through MCP.
2. Put the HUD prefab under `Canvas/Root/SafeArea`; popups spawn into `PopupRoot` with `PopupManager.Create(prefab)` (`ui-popup-anatomy`).
3. Add managers as children of `Manager`; every manager is its own prefab (`scene-authored-prefabs`).
4. Place the prefab in the boot scene, then in the other playable scenes; delete any other EventSystem.
5. Sample code: [sample-code.md](references/sample-code.md).

## 7. Done check (full script: [verify.md](references/verify.md))
Play boot -> Home -> a minigame -> Home: exactly one `GameSingleton` and one `EventSystem` in the DontDestroyOnLoad scene, `PopupManager` root non-null after Home, sort orders as the table, 0 missing scripts, empty Console, the repeated scene-flow test of `scene-teardown-safety` passes.

## Pitfalls ([pitfalls.md](references/pitfalls.md))
Second EventSystem left in the boot scene; `DontDestroyOnLoad` on a non-root child (no effect); camera or listener inside the root; one extra root canvas "just for this popup"; popups instantiated into a scene canvas; loader scripts created at runtime; copying a vendor splash root into the game root.
