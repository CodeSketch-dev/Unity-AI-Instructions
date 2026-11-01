---
name: unity-mcp-test-runner-recovery
description: "Recover when Unity MCP tests-run times out or hangs: run via TestRunnerApi in script-execute, write results to a file, avoid stale assemblies. Use when full PlayMode tests time out or give phantom failures."
triggers: tests-run timeout, testrunnerapi, stuck tests, phantom failures, stale build, results file, playmode tests
---

# MCP test runner recovery
- `tests-run` can time out on full PlayMode: start `TestRunnerApi.Execute` from `script-execute` with a result-writer callback that writes a results file (see `references/`), then poll the file.
- Stale builds: force `RequestScriptCompilation`, wait until the dll is newer than the .cs, delete the results file before each run. All tests failing with TypeLoadException = stale build.
- PlayMode leaves an unnamed empty scene: reopen the game scene before screenshots.
- After Play with domain reload off, request a script reload before EditMode.
