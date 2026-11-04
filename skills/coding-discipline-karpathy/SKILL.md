---
name: coding-discipline-karpathy
description: "Use when writing or changing code: four rules - surface assumptions, simplest code that works, surgical changes (every changed line traces to the request), goal-driven execution with verifiable success criteria. Adapted from Karpathy on LLM coding pitfalls."
triggers: assumption, overengineering, simplify, surgical, minimal diff, drive-by refactor, success criteria, test first, don dian, toi gian, sua dung cho, khong refactor ngoai pham vi
---

# Coding discipline (always on for code changes)

Inspired by Andrej Karpathy's notes on typical LLM coding mistakes (silent wrong assumptions, bloated abstractions, collateral edits). Adapted: the owner pre-approves decisions, so where the original says "ask", this studio says "decide, write the assumption down, continue" (see Autonomy rules); stop and ask only for irreversible, destructive or security-sensitive actions.

1. **Think before coding.** State assumptions and the chosen interpretation in the plan/ledger (`Ruling: ... - why - cost if wrong`). If two readings are plausible and the cost of a wrong guess is high, say both and pick one with a reason. Push back (in the plan) when a simpler approach exists. Name what is unclear instead of hiding it.
2. **Simplicity first.** Minimum code that solves the request: no extra features, no abstraction for single-use code, no configurability nobody asked for, no handling of impossible cases. If 200 lines could be 50, rewrite. Test: would a senior engineer call it overcomplicated?
3. **Surgical changes.** Touch only what the task needs. Match the surrounding style. Do not reformat, rename or "improve" adjacent code or comments. Remove only the orphans YOUR change created (unused imports/fields/functions); mention pre-existing dead code instead of deleting it, unless deletion IS the task (a cleanup or refactor task, proven by `tech-debt`). Test: every changed line traces to the request.
4. **Goal-driven execution.** Turn the task into verifiable success criteria and loop until they pass: bug -> failing test that reproduces it, then fix; feature -> tests/checks for the behaviour, then implement; refactor -> same tests green before and after. For multi-step work write `step -> verify: check` lines. Weak criteria ("make it work") are not acceptable.

Bias: caution over speed on non-trivial work; trivial one-liners need no ceremony. Pairs with `superpowers:test-driven-development`, `verification-before-completion`, `vibe-coding-guardrails`.
