---
name: tutorial-phase-system
description: "Tutorial phase system: persisted phase int, per-phase HUD visibility and locks, spotlight guidance, rewards once, resume safety. Use when building the first-time tutorial."
---

# Tutorial phase system

- Persist a phase int and per-reward flags in a `Data_Tutorial` block; each reward is granted once.
- Phases: one system introduced per phase, HUD parts hidden until introduced, currency sinks locked, optional damage protection, action within seconds, first reward within a minute.
- Guidance: arrow or line renderer plus a spotlight mask; re-show the pointer after idle.
- Resume-safe: re-entering shows the current phase; old saves migrate to done.
- No interstitials until the tutorial is done; the rating prompt and daily login appear after it.
- Phase events (`ftue_step`) go to the taxonomy.
