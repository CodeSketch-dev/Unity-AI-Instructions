---
name: auto-balance-loop
description: "Use when a generated balance plan must be simulated, tuned within a bounded iteration cap, materialized into Unity configs and verified against a fresh-save PlayMode target."
---

# Auto-balance loop

This is the pipeline gate around `auto-balance-game`. The cheap simulator narrows parameters before Unity; Unity's fresh-save golden path is the authority.

## Loop

1. Read the current GDD-generated plan and preserve observed values and explicit overrides.
2. Run `scripts/validate_balance_plan.py`; stop on structural errors.
3. Run `scripts/econ_sim.py PLAN --mode tune --out REPORT` with a hard iteration cap (default 12). A non-converged or open-world-without-milestones result is `INCONCLUSIVE`, not a pass.
4. Materialize the chosen values through the target project's config/factory layer. Fail on an unmapped discovered stat that affects completion time.
5. Run the fresh-save golden path in Unity at `timeScale = 1`; record actual milestone/completion time and currency sources/sinks.
6. If the measured result misses tolerance, change the owning config, rerun the cheapest failed gate, then run the golden path again. Keep the QA failure signature and cap retries using `qa-fix-retest-loop`.

## Evidence contract

The balance task is done only with: valid plan, simulation report, materialization mapping report, fresh-save PlayMode evidence, and measured target comparison. A simulator-only result is preparation, not gameplay balance proof.

Do not copy generic price tables into a game. GDD-observed values win, explicit user overrides win over generated values, and generated values fill only unknown tuning.
