# FoundationInstaller reference

File: `assets/FoundationInstaller.cs.txt` (copy to `Assets/_Game/Scripts/Editor/Foundation/FoundationInstaller.cs`; Editor-only, wrapped in `#if UNITY_EDITOR`). Spec it implements: `persistent-root-prefab/references/installer-spec.md`.

| Menu | Does | Idempotent behavior |
|---|---|---|
| Tools/Foundation/Install Persistent Root | writes `GameSingleton.cs` and `GameMasterInit.cs` if missing; builds or completes `Assets/_Game/Prefabs/GameSingleton.prefab`; places the instance in the open scene; removes empty stray scene EventSystems; prints canvas sort orders read back | existing children are kept, only missing ones are added; second run changes nothing |
| Tools/Foundation/Install Test Asmdefs | writes `Game.Runtime`, `Game.Editor`, `Game.Tests.EditMode`, `Game.Tests.PlayMode` asmdefs with references taken from the assemblies actually compiled into the project | existing asmdef files are kept with a warning |

Prerequisites: SketchEngine (or the project's framework with the same `MonoSingleton`) installed; for the Input System module the package `com.unity.inputsystem`; otherwise the legacy `StandaloneInputModule` is used.
Skips (reported, never guessed): framework components whose type is not found (`UISafeArea`, `PopupRootSetter`, `ViewContainer`, `FpsUnlock`).
Not installed: loading screen script and art, internet monitor, transition asset, pool and IAP components, HUD content, SDK splash.
Verify afterwards with `persistent-root-prefab/references/verify.md`; commit only when the owner asks.
Known risks (unverified, no Editor available when written): the `AssignDefaultActions` reflection call depends on the Input System version; asmdef generation fails to compile if first-party code uses assemblies not on the candidate list; adapt `candidates` to the project.
