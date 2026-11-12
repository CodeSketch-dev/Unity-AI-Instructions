---
name: qa-batch-and-fallbacks
description: "Headless Unity runs and the QA degradation ladder: MCP, batchmode, static-only. Version pin and lock checks, NUnit parsing, ECONNREFUSED path. Use when the Editor or MCP is unavailable or for local batch runner."
---

# local batch runner and fallbacks

## Ladder (print the rung in the report)
1. MCP connected: all stages.
2. MCP down, Editor closed, Unity installed: `scripts/qa_unity_batch.py` runs compile and EditMode or PlayMode tests headless.
3. No Unity: static only (`qa-static-checks`). The best verdict is STATIC-PASS; compile, wiring and play are listed as not verified.

An MCP connection error (ECONNREFUSED) is a connection failure, not a missing capability: retry once, then drop a rung and say so. Queue Editor-only work in the handoff instead of stalling.

## Batch runs
- `qa_unity_batch.py plan` prints the command; `run --yes` executes it and parses the NUnit XML. It refuses when the pinned Editor version (ProjectVersion.txt) is not installed (never open with another version: it upgrades the project) or when `Temp/UnityLockfile` shows an Editor holds the project.
- Do not run alongside an open Editor on the same folder; use a copy or close the Editor. Claim the Editor lane first (`editor-lane-single-writer`).
- Screenshots need a GPU context (no `-nographics`). On a machine without one, skip capture and report visual checks as not verified.

## Templates
local batch runner workflow, build scripts and release checklist live in `new-game-bootstrap` and `mobile-build-release`.
