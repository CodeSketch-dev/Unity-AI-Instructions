---
name: tutorial-phase-system
description: "Tutorial phase system: persisted phase int, per-phase HUD visibility and locks, spotlight guidance, rewards once, resume safety, completed flag read by monetization. Use when building the first-time tutorial."
triggers: tutorial phase, ftue, first time user, onboarding steps, tutorial step, tutorial completed, huong dan, buoc huong dan, nguoi choi moi, kt style
---

# Tutorial phase system

- Persist a phase int and a completed flag in the owning feature's Data block (`DataValue<int> TutorialPhase`, `DataValue<bool> IsTutorialCompleted`), plus per-reward flags so each reward is granted once. The reference game keeps them in each game mode's own block and has no global tutorial block; a shared `Data_Tutorial` is fine only for a single-mode game.
- Steps are `const int STEP_*` in one owner MonoBehaviour with a `CheckAndProcess()` switch and `NextStep()`; the owner destroys itself in `Awake` when the flag says completed. Step lists live in the owner/config, never as hard-coded UI paths in other classes.
- Phases: one system introduced per phase, HUD parts hidden until introduced, currency sinks locked, optional damage protection, and action/reward timing from the reference or `auto-balance-game`.
- Guidance: "tap this button" steps use the spotlight/hand overlay (`tutorial-focus-notice-hand`: focus on a rect; strict steps disable outside dismiss); "walk there" steps use the world arrow. Re-show the pointer after idle.
- Advance on the real game event, not on the overlay: subscribe to the `StaticBus` event, then `StopFocus(false)` and `NextStep()` (step-driver reference of that skill). Skip a duplicate focus while `IsFocusing`.
- Resume-safe: re-entering shows the current phase; old saves migrate to done; a skip level (progress above a named constant counts as done) is allowed for cheats and returning players.
- The completed flag gates monetization: no interstitials, native ads, rating prompt or IAP entry popups until it is true; daily login appears after it (`rating-prompt-flow`, `ads-layer-generic`).
- Phase events (`ftue_step`, `tutorial_complete`) go to the analytics taxonomy.
- Done check: a fresh save walks every step; a finished save shows nothing; kill the app mid-step and resume at the same step; every step is skippable or restart-safe.
