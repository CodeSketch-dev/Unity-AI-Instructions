# MCP-driven session loop

The orchestrator is a continuing agent loop, not a one-shot code generator. Keep working until the current gate is green, the bounded retry cap is reached, or a human taste/authority checkpoint is required.

## Iteration contract

1. Read durable state and the handoff tail. Select only skills required by the current phase/task; discovery and the index do not load skill bodies into active context.
2. Reconcile the task graph and claims. One writer owns each scene, prefab, singleton asset, and shared document. Re-read the target immediately before editing.
3. Run the cheapest applicable check first. File checks may run locally; Unity truth must come from the connected MCP adapter.
4. Dispatch from `orchestrator.py next --json`. Pass `active_skills` as skill mentions/items to the MCP subagent call, pass the task text/claims/verify as plain task data, and do not paste full unused skill bodies into the request.
5. Use MCP to inspect the actual Unity project before mutation: editor state, open scenes, target prefab/asset, Console baseline, and serialized references.
6. Apply one focused, idempotent mutation through the MCP/editor path. Save the owned asset, refresh, then re-read it.
7. Compile and run the narrowest relevant EditMode/PlayMode test. Capture concrete evidence in task state.
   When a task requires `inspection`, return the Editor readback of the source prefab/scene hierarchy and serialized references as `evidence_by_kind.inspection`; a static file check cannot satisfy it.
8. Normalize the returned result through `orchestrator.collect_result(project, task_id, result)`; reject missing `evidence_contract` or empty evidence before calling `mark`.
9. On failure, classify REAL, TEST-BUG, ENV, or FLAKY. Route REAL failures to the owning task with a stable signature, repair only that owner, and retest from the failed stage.
10. On success, mark the task only with evidence. Unload phase-specific skills before selecting the next phase set.

## MCP truth rules

- `INCONCLUSIVE` is the only valid result when required Unity MCP/editor evidence was not collected.
- A passing Python/static check cannot mark compile, serialized wiring, PlayMode, screenshot, performance, or build gates as passed.
- Never run a second Editor-lane mutation while another agent or human owns the claim.
- Do not save a stale scene or prefab: reload/re-read after external file changes before saving.
- Bound each failure signature to three repair attempts and each QA run to five iterations; escalate with the evidence summary at the cap.

## Session continuation

After each completed iteration, calculate the next ready task and continue if it has no human dependency. Do not end merely because one batch completed. End only when the requested scope is complete, blocked at the documented cap, or waiting for an explicit taste/authority decision.
