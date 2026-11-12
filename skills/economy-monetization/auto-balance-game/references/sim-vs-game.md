# Simulator versus Unity verification

The simulator is a cheap search aid, never the final balance authority.

## Required artifacts

1. `balance-plan.json`: generated values, observed facts, overrides and discovered stat bindings.
2. `simulation.json`: simulator knobs, milestone estimates, target, relative error and iteration history.
3. `materialization.json`: every generated path mapped to a Unity config/factory field; unmapped time-sensitive stats are errors.
4. `qa/reports/<date>-balance.json`: fresh-save PlayMode run at `timeScale = 1`, actual milestone/completion times, currency sources/sinks and Console result.

## Comparison

Compare each simulator milestone with the matching Unity observation. Use the GDD target tolerance when present; otherwise record the chosen tolerance as an assumption. A mismatch is a real balance failure only after confirming fresh save, normal time, deterministic seed/fixture and a reachable golden path.

When a mismatch is real, change the owning config or generated input, rerun the simulator, materialize the changed config, then rerun the failed PlayMode path. Do not loosen the validator or replace measured evidence with a simulator pass.

Open-world plans without milestones may generate config values, but they are `INCONCLUSIVE` until the GDD supplies a measurable completion/retention target or a golden-path metric.
