---
name: kcc-partner-pull-smoothing
description: "Use when two KCC characters are linked by a leash/pane/rope and the pulled one jitters: replace on/off threshold pulls with a continuous velocity-match drag and measure jitter with a headless KCC harness."
triggers: giat, jitter, keo, pull, leash, kcc, partner carry, kinematic character controller, mượt, muot, glass carry
---

# KCC partner pull without jitter

Symptom: pulled character alternates stop/go. Measured cause (carry-the-glass clone): pull computed AFTER the KCC sim step and applied as an on/off velocity next step, threshold controller + 1 step latency -> NPC speed alternated 0 / 6.5 m/s (std 2.95), leader std 1.12, separation std 0.125.
Fix that measured std 0.006 / 0.006 / 0.001:
1. Stretched (mover walks AWAY): drag the partner TOWARD the mover at the mover's own speed component along the separation, faded in over a soft zone (0.35 m) before the limit, plus a proportional correction (6 1/s) beyond the limit. Folded (mover walks INTO the partner): push the partner ahead of the mover with the same law. Watch the sign: pulling the wrong way still looks smooth when you only test walking toward the partner.
2. In the controller keep a smoothed applied pull (`Lerp(prev, target, 1-exp(-10 dt))`), subtract the previous applied pull before computing velocity, add the new one after; never a gate.
3. Measure first and after with a headless harness: AutoSimulation off, 200 steps of `PreSimulationInterpolationUpdate / Simulate / PostSimulationInterpolationUpdate` at 0.02, leader walks away, record per-step displacement std of both and separation std. Keep the harness in the repo.
Render-side (camera/pane/animator order) is a separate check; KCC interpolates in its own LateUpdate (exec order -100).
4. Test BOTH directions (away and toward) in the harness; a single scenario hid a sign bug here (leash would never have held).
