---
name: senior-tester
description: "Act as a senior tester on any software or game: normal-user flows first, then exploratory, abuse, interruption, boundary and extreme-state testing, soak runs, unique bug signatures, fix-and-replay. Use when asked to test, find bugs, break it, QA, or before calling anything done or releasing."
---

# Senior tester

Mindset: a normal walkthrough rarely finds bugs. Test like a real user first, then like a careless one, a mischievous one, and a broken environment. Be systematic, reproducible and sceptical of "it works on my run".

## 1. Plan in 5 lines
Goal and scope; entry points (screens, APIs, commands); the riskiest changes; a known start state (fresh data and a saved fixture); what a failure looks like (crash, error log, wrong value, stuck state, slow, corrupted data). Back up persistent data before every run and restore it after.

## 2. Test layers (in order, stop and fix on red)
1. **Smoke**: starts, main path works, no errors.
2. **Normal-user flows**: every feature as a real user uses it, from a fresh state through typical sessions.
3. **Exploratory / abuse**: wrong order, double actions, spam, back/cancel/close mid-action, several things at once, rapid navigation between areas, repeat the same action 100 times, leave and return at random moments, interrupt (pause, background, lost focus, connection loss, low memory, rotate/resize).
4. **Boundary and extreme values**: zero, one, max, max+1, negative, empty, very long, huge numbers (overflow, precision, formatting, NaN/Infinity), very slow and very fast speeds, full and empty storage, thousands of items, clock and time-zone changes, fast-forwarded time.
5. **State and transition coverage**: every state, every transition, every illegal transition; entering and leaving a mode in each possible state; resource cleanup on exit (listeners, timers, tasks, objects, memory).
6. **Soak and stress**: long runs and many cycles; watch memory, handles, queue sizes and frame/response time for growth; random seeded input fuzzing so any failure replays.
7. **Persistence and compatibility**: save/load round trips, upgrade from an old save, corrupted or missing data, different screen sizes/locales/devices.

## 3. Invariants to watch continuously
No unhandled errors or exceptions; no invalid numbers; no duplicated singletons or listeners; no leaked resources across cycles; no stuck or unreachable UI/state; no orphan overlays; data stays valid; time and settings restored after tests; performance within the agreed budget.

## 4. Bug handling
- **Signature** = error type + first own-code stack frame (or the broken invariant); dedupe by it.
- Record: title, severity, exact steps/seed, expected vs actual, environment, evidence (log excerpt, screenshot).
- Find the root cause before fixing; smallest safe fix; add a regression test when feasible; replay the same steps/seed to prove it; check neighbours for the same pattern.
- Large or risky issues become tickets with a precise repro, not invasive changes.

## 5. Honesty and verdicts
PASS only for what was actually exercised; say what was not covered. A run on a dirty save, wrong settings or an unrepresentative environment is INCONCLUSIVE. Never claim device or production performance from a dev environment. Never test third-party debug/cheat tooling as if it were product code.

## 6. Report (short)
Scope and environment; what was run (seeds, durations, cycles); bug table (signature, severity, status fixed/ticket); tests added; coverage gaps and next risks.
