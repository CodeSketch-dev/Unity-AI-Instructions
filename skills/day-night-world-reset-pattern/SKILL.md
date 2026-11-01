---
name: day-night-world-reset-pattern
description: "Timed day/night world cycle that resets the world at night: countdown warning, fade, safe teleport, skybox swap, locked area, reset of diggable or spawned content. Use when a game needs a periodic world reset."
triggers: day night, night reset, world reset, countdown, skybox, pit reset, epoch, lock area, ngay dem
---

# Day/night world reset
- One clock owner; phases: Day (long) -> Warning (10 s countdown toast) -> Night (short, area locked) -> Day.
- At night start: fade, move only players in the reset area to a safe spot, swap skybox, bump a world epoch, regenerate content from the epoch.
- Surface/ground must exist before anyone stands there (build colliders synchronously).
- Unlock and restore day skybox together; HUD shows timer chip and lock countdown.
- Test: repeated cycles with no leaked tweens, listeners or duplicate content (`scene-teardown-safety`).
