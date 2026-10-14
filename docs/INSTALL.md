# Installing the pipeline

Two routes. Pick one per machine; do not mix them (the same skills would exist twice).

## A. User-level install (recommended, plain skill names)
1. Double-click `sync.bat` (or run it with `/nopull`). It copies `skills/` to `~/.claude/skills` and `~/.codex/skills`, `agents/` to `~/.claude/agents`, `commands/` to `~/.claude/commands`, and the hook scripts to `~/.claude/pipeline-hooks/hooks`.
2. Hooks are not enabled automatically (settings are shared configuration). Generate the snippet and merge it into `~/.claude/settings.json` (or a project's `.claude/settings.json`):
   `py -I tools/install_hooks.py --write docs/hooks-settings.snippet.json`
3. Optional, for small context windows: merge `docs/skill-overrides.snippet.json` (`skillOverrides`, non-hub skills as `name-only`; regenerate with `py -I tools/skill_budget.py --write docs/skill-overrides.snippet.json`). At a 1M-token context everything fits.
4. Open a new session. Start a game with `/clone-game <gdd-folder>`; main thread agent: `claude --agent orchestrator`.

## B. Plugin (`.claude-plugin/plugin.json`)
`claude --plugin-dir <repo>` loads skills, agents, commands and hooks together and resolves `${CLAUDE_PLUGIN_ROOT}`. Plugin skills are namespaced (`unity-game-pipeline:<skill>`), so cross-references in the skills use plain names that only resolve in route A. Use the plugin for hooks/agents on a machine where you do not sync skills, or validate it with `claude plugin validate`.

## Checks before relying on it
- `py -I tools/skill_lint.py skills --strict` and `py -I -m unittest discover -s tools/tests` (all green).
- `py -I tools/skill_budget.py` prints listing cost against the context budget.
- Nothing is verified inside the Unity Editor until the pilot (Task 27); C# files ship as `.cs.txt` templates.

## Not installed by sync
Real SDK keys, keystores and any secrets (`new-game-bootstrap/assets/secrets.example.json` shows the placeholders).
