---
name: debug-cheats-menu
description: Dev-only cheat/debug menu (set money/zone, spawn, timeScale, reset save) with a ready IMGUI component. Use at project start or whenever testing needs fast state setup or skipping grind.
---

# Debug cheats menu

Every minute an agent or human spends grinding to reach a test state is wasted. A cheat menu turns state setup into one tap or one call, and it doubles as a reproducible test fixture.

## Setup
1. Copy `assets/DebugCheats.cs` into the project's runtime scripts (namespace `Game`; adjust to the project). It bootstraps itself after scene load, is compiled only for the Editor and development builds, resets its static registry for domain-reload-off sessions, and opens with the backtick key or a three-finger tap.
2. Each feature registers its own actions next to its code (so the menu grows with the game and never lives in one giant file):
   ```csharp
   DebugCheats.Register("Economy", "Grant test money", () => Data_Wallet.Add(configuredTestAmount));
   ```
   Register from an initialization point that runs in the Editor and dev builds (e.g. a feature's `Awake`/`OnInitialize`), not inside the game logic's hot path.
3. Wrap registrations in `#if DEVELOPMENT_BUILD || UNITY_EDITOR` when they touch real data, so release builds contain none of it.

## Standard cheat set for clones
| Group | Actions |
|---|---|
| Economy | Grant configurable test money; set income multiplier; grant offline earnings |
| Progression | set a GDD-selected stat; unlock a configured zone; set a configured feature level; trigger the selected reset/prestige flow |
| World | teleport to a configured location; spawn a GDD-defined test entity; toggle a configured safe/hazard zone |
| Time | timeScale slider (QA only; normalize before judging balance), skip N minutes of timers, set daily-reward clock |
| Save | reset save (confirmation), dump save summary to the log, load a named test save |
| Monetization | simulate ad success/failure, grant/revoke an entitlement |
| Debug | toggle FPS overlay, god mode, show colliders/paths for bots |

## Rules
- **Never in release**: the panel and registrations are compiled out; verify by checking that a release build has no `DebugCheats` types.
- **Cheats must not corrupt the save permanently by accident**: mark the session as "cheated" if a cheat modifies persisted data and make "reset save" explicit.
- **Mind game-time vs real-time**: raising `timeScale` shortens real-time timers. Verify behavior at 1x before concluding anything from an accelerated run (`unity-qa-playtest`).
- Keep actions idempotent and one-line; avoid cheats that need multi-step UI.
- Mobile: buttons sized for touch, scrollable, closable; three-finger tap must not trigger accidentally in normal play (dev builds only).

## For agents
Agents can drive the same actions in Play Mode through the Editor tooling (call the registered delegate or the underlying method) to set up a QA scenario in one call; record scenario recipes (e.g. "zone 3 + 1M money + level 5 tool") in `docs/qa/` so tests are repeatable.
