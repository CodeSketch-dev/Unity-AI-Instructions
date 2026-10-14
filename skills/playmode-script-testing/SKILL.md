---
name: playmode-script-testing
description: Verify features in Play Mode via MCP with small C# scripts (invoke onClick by reflection, read state, stretch timers) and screenshots, then restore saved data. Use for end-to-end checks when waiting or input is impractical.
---

# Play Mode script testing

Complements `unity-qa-playtest` and `done-means-wired`.

## Recipe
1. Enter Play Mode and wait until it is playing; scripts sent during the domain reload fail with a retry error: just resend.
2. Run C# with the MCP script-execute tool: it needs `public class Script { public static string Main() {...} }` and fully qualified names; return a string with the observed values.
3. Click without input automation: get the private `Button` field by reflection and call `onClick.Invoke()`. Read private state (`_autoShown`, `_busy`) the same way.
4. Stretch time instead of waiting: set a config field (countdown seconds) by reflection before opening, or set the popup private countdown to about 0.05, then check the result in the NEXT script call (a frame must pass).
5. One action per script call when a frame matters. A `Close()` inside the open animation behaves differently from a human tap: test both "immediately" and "after a moment".
6. Screenshot the Game view right after opening; crop with PIL when you need detail.
7. Persisted data (DataBlock values) changed by tests is saved with the profile: reset it at the end (tiers, timers, money) and set any reflected config back.
8. Stop Play Mode, refresh, read the Console for new errors. Exceptions caused by test shortcuts (null prefabs, missing UI services) are real findings: fix the cause, not the test.

## Report
State every path exercised (success, unclaimed, decline, failure), the values observed, and what only a device can verify (real ads, store, performance).
