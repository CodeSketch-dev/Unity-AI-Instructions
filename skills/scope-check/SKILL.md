---
name: scope-check
description: "Detect feature creep: diff current work against the plan or backlog and flag additions with their cost. Use before merging a batch, when a task grows, or on 'did we drift from the plan'."
triggers: scope check, scope creep, feature creep, drift from plan, backlog compare, out of scope, lech ke hoach, phat sinh, them tinh nang
---

# Scope check

Use at the end of a batch or when a change feels bigger than asked.

## Steps
1. Gather the intent: plan/spec/backlog item and its acceptance criteria. Gather the actual: changed files, new assets, new systems, new settings.
2. Map each change to a plan item. Unmapped changes are additions.
3. For each addition record: what, why it appeared, cost (files touched, risk to save data or perf, test burden, maintenance), and value.
4. Classify:
   - **Required fix** (the planned item breaks without it): keep, note it in the plan.
   - **Cheap and valuable** (under ~15 min, no new dependency, no data change): keep, log it.
   - **Creep**: revert or move to the backlog with a one-line description.
5. Check the reverse too: planned items silently dropped.
6. Output a short table: item | planned? | cost | decision. Apply the reverts/backlog entries yourself and continue.

## Red flags
New dependency or framework, new persistent field, a second system doing what an existing one does, UI added "while there", refactors mixed into a feature change, settings changes with no plan line.

## Verification
After reverts, compile and re-run the acceptance checks from the plan so the kept scope still passes.
