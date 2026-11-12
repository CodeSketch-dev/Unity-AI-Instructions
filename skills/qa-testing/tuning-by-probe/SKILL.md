---
name: tuning-by-probe
description: "Tune a curve, force, speed or knockback by measuring the real outcome first: seeded probe, before/after table, reference shape scaled to the world, bounds tests. Use before editing any gameplay curve or number copied from a reference."
---

# Tuning by probe

- Never tune from reading code: formulas hide multipliers (a reference multiplier once differed 5x from code defaults).
- Write a probe (Editor/Play script) measuring the real outcome (landing distance, time, speed) per case; seeded, 3 trials; print a table before and after.
- Measure the reference too if available; copy its SHAPE, scale amplitude to this world's size.
- Add tests: monotone in input, within bounds, cap respected, no NaN/Infinity.
- Sweep extremes (min/max values, all headings) for tunnelling and out-of-map; assert max per-frame step.
- Report the table and chosen constants. See `senior-tester`, `profiling-evidence`.
