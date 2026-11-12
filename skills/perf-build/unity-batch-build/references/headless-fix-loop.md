# Headless fix loop (claude -p)

Use only where judgement is needed. Local build, test and signing stay deterministic scripts. Deployment and upload are outside this pipeline.

```powershell
claude -p "Read Logs/test-edit.log and Logs/build.log. Fix only compile errors caused by files changed in this branch. Do not touch ProjectSettings, scenes, prefabs or keystores. Do not commit." `
  --allowedTools "Read,Edit,Grep,Glob,Bash(git diff:*),Bash(git status:*)" `
  --max-turns 12 --output-format json > Logs/claude-fix-1.json
```

Loop contract:
1. Run the failing gate; if it passes, stop.
2. Iteration cap: 3 for compile errors, 2 for test failures. One claude call per iteration, then rerun only the failing gate.
3. After the cap: stop, keep the logs as artifacts, mark the job failed. No endless retries.
4. Wall-clock timeout on the step. Check `claude --help` for a spend cap flag in the installed version before relying on one.
5. Fixes land as a working-tree diff on a branch for human review; nothing is merged or pushed automatically.
6. Never use permission-skipping flags. The tool allow-list above is the safety boundary.

Other good headless uses: release notes from `git log`, store listing drafts into `docs/store/`, log triage (`unity-log-triage`), diff review before release. Not for signing, upload, publishing, deployment or changing project settings.

If the repo also runs the Unity MCP bridge, local batch runner should build from a manifest without it (dev-only dependency) so the player build has no editor tooling.
