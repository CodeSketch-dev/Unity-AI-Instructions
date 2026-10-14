---
description: Lint a GDD folder and list the BLOCK, WARN and open questions.
argument-hint: <path-to-gdd-folder>
---
Run `py -I <skills>/game-orchestrator/scripts/gdd_lint.py $ARGUMENTS`. Show BLOCK findings first with the exact file and field, then WARN assumptions, then the open questions from `_generated/questions.md` (batches of 4 with a recommended default). Do not edit the GDD unless asked.
