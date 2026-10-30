---
name: graphify-workflow
description: Always-on for Unity projects - at session start bootstrap Graphify (install, build graph, start the single watcher) without asking, and prefer graphify query/path/explain over reading code. Also covers scope, auto-update and watcher fixes. Install, scope, auto-update and query a local code-only Graphify knowledge graph for a Unity project (Windows, free, no LLM). Use when adding Graphify to a Unity repo, when the graph is stale or the watcher misbehaves, or before scoping a large C# codebase with query/path/explain.
---

# Graphify workflow (always on, no prompt needed)

## Session-start bootstrap (do it without asking the user)
1. `graphify --version`. Missing -> `uv tool install graphifyy --with watchdog` (install uv first if absent; no Graphify Cloud, no API keys).
2. Unity project (has `ProjectSettings/`) with no `graphify-out/graph.json` -> create `.graphifyignore` + `.gitignore` entry (see Scope), run `graphify install --project --platform claude` once, copy `scripts/graphify_watch.py` and `scripts/graphify_ctl.sh` from this skill into `<repo>/docs/tools/` (adjust the project folder name in the ctl script), then `graphify update .` and `bash docs/tools/graphify_ctl.sh start`.
3. Graph exists -> `bash docs/tools/graphify_ctl.sh status`; dead watcher -> `restart` (never start a second one; the lock prevents it). After a pull/branch switch run `... update`.
4. Prefer `graphify query/path/explain/affected` to scope code before Read/Grep. Fallback to Read/Grep when the graph is missing, empty, stale or errors. Never load GRAPH_REPORT.md/graph.json. INFERRED edges are unverified. Graphify never replaces Unity MCP.
5. Do not commit or delete anything while bootstrapping; legacy `graphify-out` folders that are tracked or under `Assets/` are reported, not removed.

# Graphify for Unity (code-only, local)

Package `graphifyy` (CLI `graphify`). AST-only for C#: no API key, no Graphify Cloud, no LLM calls. Always run `graphify --help` first; flags change between versions.

## Install (Windows)
- `uv tool install graphifyy --with watchdog` (watchdog is NOT bundled; without it no watcher). Re-run with `--force` to upgrade.
- Project skill + Claude hooks: `graphify install --project --platform claude` (run in the Unity project root). It appends a `## graphify` section to CLAUDE.md and adds PreToolUse `hook-guard` hooks (reminders only unless `--strict`). Replace that section with a short one: query/path/explain first, fallback to Read/Grep, never load GRAPH_REPORT.md/graph.json, INFERRED edges are unverified, graphify does not replace Unity MCP, one watcher owns updates.
- The graphify package ships its own skill named `graphify`; name project notes differently.

## Scope (`<unity>/.graphifyignore`, gitignore syntax)
Exclude Library, Temp, Obj, Logs, Build(s), UserSettings, MemoryCaptures, .git, `*.csproj`, `*.sln*`, `*.md`, `docs/`, agent folders (`.claude`, `.codex`, `.agents`), and vendor code under Assets (SDKs, Odin, TMP, plugins, art packs). Keep first-party `Assets/_Game`. Add `/graphify-out/` to the Unity `.gitignore` (derived, per checkout). If an old graph output sits inside `Assets/`, Unity imports it: never leave `graphify-out` under Assets (build with root = project dir, not Assets).

Build: `graphify update .` (about 1 min for ~1500 C# files, ~20k nodes). Check with `graphify query "<ClassName>"`; nodes carry `src=<file> loc=L<n>`.

## Auto-update: one watcher
`graphify watch .` recurses the whole project (Library churn) and needs a held terminal. Prefer a small managed watcher:
- watch only first-party code dirs (`Assets/_Game`), `.cs` only, debounce 5 s, then `graphify update <root>` at below-normal priority (graphify has its own rebuild lock, so concurrent updates from agents/hooks are safe).
- **Deleted/moved files**: plain `graphify update` keeps ghost nodes (shrink guard). The watcher adds `--force` for batches containing delete/move events.
- Single instance via a byte-range `msvcrt.locking` lock file plus pid file in `graphify-out/`; ctl script `start|stop|restart|status|update` launching `pythonw -I -u` hidden with log redirect. Reference implementation: `docs/tools/graphify_watch.py` and `graphify_ctl.sh` in thunder-break-egg.
- Trap: launch Python with `-I`. A stray `copy.py`/`json.py` in cwd or %TEMP% broke the watchdog native import and silently fell back to a polling observer that missed create/delete events.
- Updates take 13-40 s while Unity compiles; wait before asserting a test failed.
- The graph lives in each checkout's own `graphify-out/`, with relative paths. Worktrees/branches therefore never mix versions; run one watcher per worktree. After a branch switch run `ctl update` (git hooks: inspect `.git/hooks` and `core.hooksPath` first; `graphify hook install` must not overwrite existing hooks).

## Use
`graphify query "<q>"`, `path "A" "B"`, `explain "X"`, `affected "X"`, `god-nodes`. Then Read only the pointed files. Exit codes: 3 ambiguous, 4 no match. Fall back to Read/Grep if the graph is missing/stale/errors. Never load GRAPH_REPORT.md or graph.json into context. INFERRED edges are unverified. Graphify does not know scenes, prefabs, ScriptableObjects or compile state: use Unity MCP for those.

## Verify (done means)
Class found by query; throwaway `.cs` appears after the debounce; deleting it removes it; stop/start works with a single pid; Unity Console shows no new errors (take the Editor lock before touching Assets).
