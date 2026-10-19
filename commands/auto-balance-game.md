---
description: Generate a complete topology-neutral balance plan with repeatable milestones, constraints and stat overrides.
argument-hint: --full-days N --hours-per-day H [--milestone PATH=TIME ...] [--constraint PATH=VALUE ...] [--set PATH=VALUE ...] --out PATH
---
Run `py -I <skills>/auto-balance-game/scripts/auto_balance_game.py $ARGUMENTS`. Then run `py -I <skills>/auto-balance-game/scripts/validate_balance_plan.py <out>`. Report the generated plan path, target timeline, milestone allocation, discovered stats, assumptions, and validation errors. Pass repeatable parameters through unchanged; do not require a biome list or collapse the result into a hand-written economy table.
