---
name: unity-qa-playtest
description: Plan and run QA for a feature or build: test matrix, Play Mode via MCP, aspect ratios, fresh/saved data, interruptions, perf sanity, bug reports. Use on "test it", "QA this", before milestones or human playtests.
---

# Unity QA playtest

Testing is cheap when the plan is derived from the features and the checks are repeatable. Agents can run the Editor-level matrix; real-device checks go to the human with a precise checklist.

## 1. Build the test matrix
From `docs/clone-plan.md` / the feature inventory create `docs/qa/test-matrix.md`: rows = features, columns = scenarios.
Scenarios to include for every feature:
- Happy path, first use (fresh save / FTUE state), repeat use.
- Boundaries: zero/max currency, full/empty slots, locked/unlocked, max level.
- State transitions: disable/enable, scene reload, die/respawn, enter/leave zones quickly.
- Save/load: change state -> exit Play -> re-enter -> persisted correctly; corrupt/empty save handled.
- Input/UI: touches on overlapping UI, simultaneous touches, popups opening during actions.
- Resolution/aspect: 9:16, 9:20, 3:4; safe area (`mobile-hud-layout`).
- Interruptions: app pause/resume, back button (Android), low-memory behavior, audio focus.
- Timing: very short and very long sessions, offline reward, clock changes if rewards use time.

## 2. Run in the Editor (MCP)
- Baseline Console; enter Play; execute each scenario with the debug/cheat menu to jump state quickly; capture the Console and a screenshot per failure.
- Watch for: NullReference/Missing references, errors on exit Play, leaked objects (count growth after repeating an action 50-100 times), event listeners not unsubscribed, tweens left running.
- Performance sanity: frame time and GC allocations in a busy scene via profiler stats (not a substitute for device tests; see `mobile-perf-audit`).

### Fast-forward harness rules
- Raise `Time.timeScale` only for QA and normalize results back to normal speed before judging balance or feel.
- **Game-time vs real-time**: gameplay timers (e.g. a hatched pet lifetime of 40 game-seconds) shrink in real time under timeScale 60 (about 0.7 real seconds), so a bot/route may "miss" things that work at 1x. Verify the path at timeScale 1 first; for accelerated runs act in the same frames or lengthen those timers only for the QA run.
- **Fresh state**: clear the save from the project's exact persistent data directory (company/product name path), then confirm defaults were recreated (levels, money). Never claim new-player completion time from a polluted save.
- A route harness must cover the whole loop (collect -> carry -> place -> income -> upgrades -> boss exposure -> zone progression), not just one segment; if a step yields zero results (e.g. eggs broken but 0 pets), trace the event path and confirm an active target before concluding anything.
- Another agent or the human may stop Play Mode or change timeScale mid-run; re-check state and rerun instead of trusting partial output.

## 3. Device checklist for the human
Provide a short list: install the dev build, play the first 5 minutes, perform N specific actions, check heat/battery/FPS feel, try rotating/notch/gesture area, background the app and return, airplane mode if ads exist. Ask for answers in a few words per line.

## 4. Bug report format
`Title` / `Build or commit` / `Steps` / `Expected` / `Actual` / `Frequency` / `Evidence` (Console text, screenshot) / `Suspected area`. One bug per entry in `docs/qa/bugs.md`; update status when fixed and verified.

## 5. Fixing
Use `unity-debugging` to find root cause; re-run the failing scenario and neighbors; add the scenario to the matrix so it stays covered.

## Report
Pass/fail counts, new bugs, what was not tested (and why), and what needs a device.
