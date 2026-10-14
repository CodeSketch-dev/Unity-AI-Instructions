---
description: Run the QA gate for the current phase and record evidence.
---
Use the `qa-fix-retest-loop` skill (scripts in `qa-static-checks`: start with `qa_run.py static --scope diff`, record every stage with evidence, finish with `qa_run.py verdict`) for the current phase of the orchestrator state: run the static scans, validators and tests that gate this phase, read the Unity Console, and mark the gate tasks with evidence through `orchestrator.py mark`. Follow the iteration cap; at the cap escalate with a one-screen summary instead of looping.
