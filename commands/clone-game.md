---
description: Build a Unity game from a GDD folder end to end with the pipeline (lint, plan, dispatch, gates).
argument-hint: <path-to-gdd-folder>
---
Use the `game-orchestrator` skill with the GDD at $ARGUMENTS.
1. Run `gdd_lint.py` on it. Any BLOCK: switch to `gdd-intake` to resolve it with the human (batched questions, defaults recommended).
2. Run `orchestrator.py init` for this project, show the one-page H1 summary (systems, P0/P1/P2 counts, assumptions, estimated hours) and wait for approval.
3. Then loop `next` -> dispatch -> collect -> `mark` with evidence, following the phases and gates. Stop only for taste checkpoints or destructive/outward actions.
Report in Vietnamese, tersely; files and code in English.
