---
name: senior-tester
description: "Act as a senior tester on any software or game: normal-user flows first, then exploratory, abuse, interruption, boundary and extreme-state testing, soak runs, unique bug signatures, fix-and-replay. Use when asked to test, find bugs, break it, QA, or before calling anything done or releasing."
---

# Senior tester

A normal walkthrough rarely finds bugs: test like a real user, then a careless one, a mischievous one, a broken environment. Be reproducible and sceptical of "works on my run".

## Plan (5 lines)
Scope; entry points; riskiest changes; known start state (fresh data + saved fixture); what failure looks like (crash, error log, wrong value, stuck state, slowness, corrupt data). Back up persistent data before each run, restore after.

## Layers (in order, fix on red)
1. **Smoke**: starts, main path works, no errors.
2. **Normal flows**: every feature as a real user, fresh state, typical sessions.
3. **Abuse**: wrong order, double/spam actions, back/cancel mid-action, simultaneous actions, rapid navigation, 100x repeats, random leave/return, interrupts (pause, background, focus loss, connection loss, rotate/resize).
4. **Boundaries**: 0, 1, max, max+1, negative, empty, very long, huge numbers (overflow, precision, formatting; NaN/Infinity/-1/1e100 into every number formatter), slow/fast speeds, full/empty storage, thousands of items, clock changes.
5. **State coverage**: every state, transition and illegal transition; enter/leave each mode from each state; cleanup on exit (listeners, timers, tasks, objects).
6. **Soak**: long runs, many cycles; watch memory, handles, queues, frame time for growth; seeded random input so failures replay.
7. **Persistence**: save/load round trip, old save upgrade, corrupt/missing data, other screens/locales/devices.

## Invariants
No unhandled errors; no invalid numbers; no duplicate singletons/listeners; no leaks across cycles; no stuck UI/state or orphan overlays; valid data; time/settings restored; performance in budget.

## Bugs
- Signature = error type + first own-code frame (or broken invariant); dedupe by it. Record steps/seed, expected vs actual, environment, evidence.
- Root cause before fix; smallest fix; regression test; replay the same seed; grep neighbours for the pattern. Risky issues become tickets.
- **Red test triage**: STALE (design changed on purpose: rewrite to the current contract with a why comment) or REGRESSED (fix code). Never delete or loosen; keep a verdict table.
- **Tuning**: see `tuning-by-probe`. Speed/physics sweep: step through values and headings, assert max step per frame, no out-of-bounds, no NaN.
- Static checker output: sort into real / false positive / needs screenshot before fixing.

## Verdicts and report
PASS only for what was exercised; list gaps. Dirty save, wrong settings or unrepresentative environment = INCONCLUSIVE. No device claims from a dev environment. Report: scope, runs (seeds, durations), bug table (signature, severity, status), tests added, gaps.
