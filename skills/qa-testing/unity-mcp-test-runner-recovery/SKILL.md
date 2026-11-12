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
- Run PlayMode in small class groups (Filter groupNames/testNames), delete the results file first, wait for "done pass=N fail=M"; a full run can hang >10 min.
- Order-dependent PlayMode failures with domain reload off: suspect a persistent singleton (`PersistAcrossScenes`) whose reloaded-scene duplicate self-destroys. `Find()` helpers using FindFirstObjectByType can return the doomed duplicate (destroyed input/audio); prefer `HasInstance ? Instance : Find...`. Diagnose with a state probe, do not guess static leaks.

- EditorApplication.isCompiling can stay true for minutes after a Hot Reload package change while the log shows "Finished compiling" and scriptCompilationFailed is false: check the Editor.log tail, then enter Play anyway instead of polling forever.

- Hot Reload trap: with a Hot Reload package installed, editing a const may never rebuild the runtime DLL (its timestamp stays old) and bakes keep the old value. Check Library/ScriptAssemblies/<asm>.dll mtime; if older than the edit, CompilationPipeline.RequestScriptCompilation(CleanBuildCache), then read the const back before baking.

## Waiting for results
The results file holds "running" while tests execute and a "done pass=N fail=M" line at the end; poll for the `^done` line, not the file mtime (a fresh "running" file passes any mtime check and a stale "done" file from a previous run looks finished). Delete or overwrite it before starting a run.
