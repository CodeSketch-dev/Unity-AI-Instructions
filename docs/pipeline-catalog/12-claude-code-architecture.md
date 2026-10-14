# 12 - Claude Code architecture for the AI game pipeline

Status: read-only design research, 2026-10-15, by the `claude-code-guide` subagent (it had no write tool; the parent saved its returned text verbatim apart from the harness wrapper). Nothing was installed, run, or edited. No Unity Editor or MCP session was used.

Scope: how the pipeline in `docs/superpowers/specs/2026-10-15-ai-game-pipeline-design.md` maps onto Claude Code features: skills, subagents, hooks, plugins, memory, headless `claude -p`, token cost.

Tags: **VERIFIED** = read in an official doc page or repo file (cited). **INFERRED** = design judgment; test before relying. **NOT READ** = linked page not opened.

Sources (read 2026-10-15): https://code.claude.com/docs/en/skills, /sub-agents, /hooks, /hooks-guide, /plugins/create, /memory, /headless, /cli-reference, /context-window. Not read: /prompt-caching, /plugin-evals, /agent-sdk/overview. This design uses only the CLI unless noted.

---

## 1. Verified capability table

| # | Capability | Fact | Status | Source |
|---|---|---|---|---|
| C1 | Skill frontmatter | Fields: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context` (`fork`), `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility`. Unknown fields ignored silently. | VERIFIED | skills |
| C2 | Description budget | `description` + `when_to_use` truncated at 1,536 chars in the listing. | VERIFIED | skills |
| C3 | Listing budget | Listing scales at 1% of context window. Every skill name always listed. Over budget, descriptions dropped starting with least-invoked skills. Override: `skillListingBudgetFraction` or env `SLASH_COMMAND_TOOL_CHAR_BUDGET`; per-skill cap `skillListingMaxDescChars`; `"name-only"` in `skillOverrides`. | VERIFIED | skills |
| C4 | Progressive disclosure | `SKILL.md` under 500 lines. Supporting files load only when read. Body loads only when invoked. `scripts/` executed, not loaded. | VERIFIED | skills |
| C5 | Zero-cost manual skills | `disable-model-invocation: true` keeps the skill out of the listing until `/name`. | VERIFIED | skills; context-window |
| C6 | Skill locations | Enterprise, `~/.claude/skills/`, `.claude/skills/`, nested, `--add-dir`, plugin `<plugin>/skills/`. Precedence enterprise > personal > project. Plugin skills namespaced `/plugin-name:skill-name`. | VERIFIED | skills |
| C7 | Skill after compaction | `/compact` re-injects each invoked skill body capped at 5,000 tokens per skill. Listing not re-injected. | VERIFIED | context-window |
| C8 | Malformed frontmatter | Body loads with empty metadata, so no description matching. `claude plugin validate <dir>` finds it. | VERIFIED | skills; CLI reference |
| C9 | Subagent frontmatter | Required `name`, `description`. Fields: `tools`, `disallowedTools`, `model` (`sonnet`,`opus`,`haiku`,`fable`, full ID, `inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation` (`worktree`), `color`, `initialPrompt`, `omitClaudeMd`, `autoCompactWindow`, `experimental`. | VERIFIED | sub-agents |
| C10 | Subagent `skills` | Full content of listed skills injected at startup, first 32 names. Does not restrict access. Skills with `disable-model-invocation: true` cannot be preloaded. | VERIFIED | sub-agents |
| C11 | Subagent memory | `memory: user\|project\|local` -> `~/.claude/agent-memory/<name>/`, `.claude/agent-memory/<name>/`, `.claude/agent-memory-local/<name>/`. First 200 lines / 25 KB of `MEMORY.md` load. Read/Write/Edit auto-enabled. `project` recommended. | VERIFIED | sub-agents |
| C12 | Plugin subagent limits | In plugin-shipped agents, `hooks`, `mcpServers`, `permissionMode` are ignored. | VERIFIED | sub-agents |
| C13 | Subagent isolation | Own context window; loads CLAUDE.md and MCP/skills; no conversation history; result returns to parent. | VERIFIED | context-window |
| C14 | Subagent nesting | Default depth three layers. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` disables nesting. Omit `Agent` from `tools` to stop spawning. `Agent(type)` allowlists apply only to the main-thread run with `claude --agent`. | VERIFIED | sub-agents |
| C15 | Hook events | PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, UserPromptSubmit, UserPromptExpansion, Stop, StopFailure, SubagentStart, SubagentStop, SessionStart, SessionEnd, Setup, PreCompact, PostCompact, PermissionRequest, PermissionDenied, Notification, TaskCreated, TaskCompleted, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, DirectoryAdded, FileChanged, WorktreeCreate, WorktreeRemove, PreModelSwitch, PostModelSwitch, Elicitation, ElicitationResult, MessageDisplay. | VERIFIED | hooks |
| C16 | Blocking events | Exit 2 blocks on: PreToolUse, UserPromptSubmit, UserPromptExpansion, Stop, SubagentStop, TeammateIdle, TaskCreated, TaskCompleted, ConfigChange (not policy), PostToolBatch, PreCompact, PreModelSwitch, Elicitation, ElicitationResult. Not honored for PermissionRequest. PostToolUse cannot undo a tool that ran. | VERIFIED | hooks |
| C17 | Exit-code rule | Exit 0: stdout parsed as JSON if a single object. Stdout added as context only for UserPromptSubmit, UserPromptExpansion, SessionStart, PostModelSwitch. Other exit codes are non-blocking errors. Enforcement needs exit 2 or JSON `permissionDecision`. | VERIFIED | hooks |
| C18 | Hook JSON output | Universal: `continue`, `stopReason`, `systemMessage`. Decisions: top-level `decision:"block"` + `reason`; `hookSpecificOutput.permissionDecision` = allow/deny/ask/defer on PreToolUse, plus `permissionDecisionReason`, `updatedInput`, `additionalContext`. | VERIFIED | hooks |
| C19 | Hook matchers | `*`/empty/omitted = all. Letters, digits, `_`, `-`, space, `,`, `\|` = exact or list. Other chars = unanchored JS regex (`mcp__unity-mcp__.*`). `if` uses permission-rule syntax e.g. `Bash(git push *)`. | VERIFIED | hooks |
| C20 | Hook types | `command`, `http`, `mcp_tool`, `prompt`, `agent` (experimental). | VERIFIED | hooks |
| C21 | Hook timeouts | Default 600 s command/http/mcp_tool; 30 s prompt; 60 s agent. 30 s for command/http/mcp_tool on UserPromptSubmit and model switch. | VERIFIED | hooks |
| C22 | Hook env vars | `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` exported to hook processes. | VERIFIED | hooks |
| C23 | Hooks vs memory | CLAUDE.md is context, not enforcement. Must-hold rules belong in a hook. Skill-scoped hooks via skill `hooks:`. | VERIFIED | memory; skills |
| C24 | CLAUDE.md locations | `./CLAUDE.md` or `.claude/CLAUDE.md`, `~/.claude/CLAUDE.md`, org managed, `CLAUDE.local.md`. Claude can read `AGENTS.md` in place of CLAUDE.md. | VERIFIED | memory |
| C25 | CLAUDE.md size/import | Target < 200 lines per file. `@path` imports expand at launch and do not reduce context cost; max depth four hops. | VERIFIED | memory |
| C26 | Path-scoped rules | `.claude/rules/**/*.md`; `paths:` frontmatter loads a rule only when matching files are touched. `~/.claude/rules/` applies to all projects. | VERIFIED | memory |
| C27 | Auto memory | `MEMORY.md` + topic files per repo, shared across worktrees. First 200 lines / 25 KB load each session. | VERIFIED | memory; context-window |
| C28 | Headless | `claude -p`. Flags: `--output-format text\|json\|stream-json`, `--json-schema`, `--max-turns`, `--max-budget-usd`, `--allowedTools`, `--disallowedTools`, `--permission-mode` (default/acceptEdits/plan/auto/dontAsk/bypassPermissions/manual), `--permission-prompts none` (v2.1.259+), `--settings`, `--mcp-config`, `--strict-mcp-config`, `--plugin-dir`, `--continue`, `--resume <id>`, `--include-hook-events`, `--model`, `--effort`, `--agents`, `--append-system-prompt-file`. Exit 0 success, non-zero failure; SIGTERM 143. | VERIFIED | headless; CLI reference |
| C29 | Bare mode | `--bare` skips auto-discovery of hooks, skills, commands, subagents, plugins, MCP, auto memory, CLAUDE.md. Requires `ANTHROPIC_API_KEY`. Recommended for scripted calls. | VERIFIED | headless; CLI reference |
| C30 | Headless cost fields | `--output-format json` has `total_cost_usd` and per-model breakdown (client estimate); `session_id` for `--resume`. | VERIFIED | headless |
| C31 | Stream init event | `system/init` lists `plugins`, `plugin_errors`, `mcp_servers`, `mcp_server_errors`. local batch runner can fail when non-empty. | VERIFIED | headless |
| C32 | Unattended permissions | `--permission-prompts none` denies unresolved prompts. `dontAsk` denies anything not pre-allowed. Denials appear in stream output. | VERIFIED | headless; CLI reference |
| C33 | Plugin layout | `.claude-plugin/plugin.json` only manifest there. Components at root: `skills/<name>/SKILL.md`, `agents/*.md`, `hooks/hooks.json` (top-level `"hooks"` key), `.mcp.json`, `commands/` (legacy). | VERIFIED | plugins/create |
| C34 | Plugin dev loading | `claude --plugin-dir ./dir` (repeatable, `.zip`, folder of plugins v2.1.265+). `--plugin-url`. `CLAUDE_CODE_PLUGIN_DIRS` (v2.1.280+). `/reload-plugins`. | VERIFIED | plugins/create; CLI |
| C35 | Plugin validation | `claude plugin validate <path>` checks manifest + frontmatter of skills/agents/commands; `--strict` fails on warnings; works on `.claude/skills`. | VERIFIED | plugins/create; skills |
| C36 | Personal plugin | `claude plugin init <name>` scaffolds under `~/.claude/skills/<name>/`, auto-loads as `<name>@skills-dir`. | VERIFIED | plugins/create |
| C37 | Plugin evals | `claude plugin eval [target]` runs cases in isolated `claude -p` sessions with/without the plugin. `evals/<case>/prompt.md` + `graders/*.md`. Exit 0 all meet threshold (default 1.0), 1 below, 2 partial (cost ceiling/auth). `--json`, `--max-cost-usd`, `--trust-plugin`, `--concurrency`. Gated by server-side kill switch. | VERIFIED (embedded reference) | plugin-evals page NOT READ |
| C38 | Plugin hooks scope | Plugin `hooks/hooks.json` apply whenever the plugin is enabled. | VERIFIED | sub-agents; plugins/create |
| C39 | Context costs at start | System prompt, auto memory head, env info, deferred MCP tool names, skill listing, CLAUDE.md. MCP schemas deferred by default; `ENABLE_TOOL_SEARCH=auto` loads them if they fit 10% of context. | VERIFIED | context-window |
| C40 | Plugin enable mid-session | Mid-conversation load/unload can invalidate prompt cache, so held until `/reload-plugins`. | VERIFIED | plugins/create; headless |
| C41 | Prompt caching | Dedicated page exists; not read. | NOT READ | /prompt-caching |
| C42 | Repo sync script | Repo has `sync.bat` only: copies `AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, copies `skills\*` to `~/.claude/skills\` and `~/.codex\skills\`, backs up differing files, `git pull --ff-only` only when clean. No `sync.ps1` exists although the memory index mentions one. | VERIFIED (repo file) | `sync.bat` |

Not verified by a fetched page: exact skill-name character rules, exact `permissions.deny` syntax for `Edit(...)`, `--max-turns` with `--resume`, whether `--settings` hooks run under `--bare`. Treated as INFERRED below; test them.

---

## 2. Plugin packaging vs current sync.bat

Current: `sync.bat` deploys personal copies (`~/.claude/CLAUDE.md`, `~/.claude/skills/<name>/`); skills are unprefixed (`/unity-ui`). VERIFIED (C24): Claude reads `AGENTS.md` directly, but the user-level copy is still needed for global rules.

Plugin option: a plugin `unity-game-pipeline` gives `/unity-game-pipeline:unity-ui` (C6, C33). Renaming existing skill references is the biggest cost. Plugin subagents ignore `permissionMode`, `hooks`, `mcpServers` (C12), so permission mode must come from project/user settings. Plugins are versioned, installable elsewhere, and give one place for `plugin validate` / `plugin eval`.

Recommendation (INFERRED):
1. Keep `sync.bat` as the dev deploy and point it at the new tree. Add `sync.ps1` only if wanted; none exists.
2. Build the same tree as a plugin from day one, loaded with `--plugin-dir`; publish after the pilot.
3. Subagent permission modes go in project `.claude/settings.json` or local batch runner settings.
4. Decide the skill prefix before writing skills.

### Plugin layout tree (proposed)

```text
unity-game-pipeline/                     plugin root
├─ .claude-plugin/plugin.json            name, version, description (only file here)
├─ skills/                               ~20-40 listed hub skills
│  ├─ pipeline-router/SKILL.md           GDD intake, phase order, handoff
│  ├─ unity-ui/ (SKILL.md + references/)
│  ├─ unity-gameplay/  unity-economy/  unity-data-factory/  unity-perf-mobile/
│  ├─ unity-art-import/  game-designer-gdd/  qa-harness/  release-checklist/
├─ agents/                               orchestrator, game-designer, tech-lead, gameplay-dev,
│                                        ui-dev, art-tech, economy-balancer, qa-tester,
│                                        perf-auditor, release-engineer, reviewer (.md)
├─ hooks/hooks.json                      paths use ${CLAUDE_PLUGIN_ROOT}
├─ tools/                                py -I scripts, executed not loaded
│  ├─ lint_skills.py   hooks/ (protect_files, mark_dirty, stop_gate...)
│  ├─ ci/ (gate.py, run_pipeline.ps1)    unity/ (batch compile, screenshot)
├─ evals/<case>/prompt.md, graders/*.md
└─ README.md
```

Per-project files (not in the plugin): `AGENTS.md` (overrides only), `.claude/settings.json`, `.claude/rules/*.md` (with `paths:`), `docs/agent-handoff.md`, `docs/feedback-notes.md`, `docs/pipeline/{gdd.yaml,balance-targets.json,run-state.json}`.

---

## 3. Skill-library design and lint spec

### The 1,000-skill problem
- VERIFIED (C3): every skill name is always listed; budget 1% of context; descriptions dropped for least-invoked skills first.
- INFERRED: 1,000 listed skills cost thousands of tokens each session and routing degrades. Measure with `/doctor` or `/context` first.
- VERIFIED (C5): `disable-model-invocation: true` removes a skill from the listing; manual `/name` only; cannot be preloaded (C10).

### Decision: many recipes, few listed skills
- List ~20-40 hubs, each with sharp `description` + `when_to_use`; recipes are `references/*.md` (1,000+ files cost nothing until read, C4).
- Hubs are model-invocable so subagents can preload them; each hub lists its references one line each and says when to `Read` one.
- Side-effect skills get `disable-model-invocation: true`.
- SKILL.md < 500 lines, ideally < 150; critical instructions first because only the start survives compaction (C7).
- `skillOverrides` `"name-only"` for low-priority hubs if the listing overflows.

Hub frontmatter template:
```yaml
---
name: unity-ui
description: Build Unity uGUI screens for mobile games - canvas setup, HUD zones, popups, panels, buttons, joystick, safe area, banner clearance. Use for any screen layout work.
when_to_use: Create/modify Canvas, HUD, popup, panel, tab, list, toast, button layout. Triggers "make a popup", "fix HUD layout", "shop screen".
---
```

### Lint spec (`tools/lint_skills.py`, run `py -I tools/lint_skills.py <dir>`)

| Rule | Check | Severity | Why |
|---|---|---|---|
| L1 | `SKILL.md` exists in each dir; dir name lowercase-hyphen | error | routing / `/plugin:skill` naming |
| L2 | YAML parses; `name` equals dir name | error | C8 |
| L3 | Unknown frontmatter keys | error | silently ignored (C1) |
| L4 | `description` non-empty; description+when_to_use <= 1,536 chars | error / warn at 1,200 | C2 |
| L5 | Description starts with use case, not "This skill..." | warn | truncation drops tail |
| L6 | SKILL.md <= 500 lines; warn at 150 | error / warn | C4 |
| L7 | Every `references/*.md` linked; no orphans | warn | dead weight |
| L8 | Every relative path resolves | error | broken disclosure |
| L9 | `disable-model-invocation: true` when body has side-effect verbs (build, deploy, submit, delete, commit, push) | warn | C5 |
| L10 | No subagent `skills:` entry points at a manual-only skill | error | C10 |
| L11 | Estimated listing cost vs budget | info / warn at 80% | C3 |
| L12 | Forbidden stale names: `CodeSketchDebug`, `Utils` (must be `Utility`), `LeanPool`, `PoolManager` (must be `PoolPrefabGlobal`/`Pool_Manager`) | error | contradictions 1-2 in `docs/pipeline-catalog.md` |
| L13 | A SketchEngine skill may not mention `OptCollisionRegister<T>`; a CodeSketch skill may not mention `INSTANCE` | error | AGENTS "never mass-replace" |

Trigger tests: one `plugin eval` case per hub with a `tool_used` grader on `Skill`. Gate lint via hook H7.

---

## 4. Subagent roster and frontmatter drafts

Rules: orchestrator runs as the main thread (`claude --agent orchestrator`) because `Agent(type)` allowlists only apply there (C14); leaves omit `Agent`. Leaves preload hubs only (C10). At most one writer per scene/prefab (INFERRED). `isolation: worktree` is slow for Unity (own Library); use for pure C# only (INFERRED). Models (INFERRED): opus for orchestrator/tech-lead/reviewer, sonnet for implementers/QA, haiku only for scripted log triage. `memory: project` for agents that accumulate repo knowledge.

| Agent | Role | Writes | Model | Preloads |
|---|---|---|---|---|
| orchestrator | phases, run-state, caps | docs/pipeline, handoff | opus | pipeline-router |
| game-designer | GDD -> feature inventory, balance targets | docs/pipeline | sonnet | game-designer-gdd |
| tech-lead | framework map, architecture, task split | docs/pipeline, plans | opus | unity-data-factory |
| gameplay-dev | gameplay code + prefabs via MCP | Scripts/Logic | sonnet | unity-gameplay, unity-perf-mobile |
| ui-dev | screens via idempotent builder | Scripts/Logic/UI, prefabs | sonnet | unity-ui |
| art-tech | import, materials, shaders | Assets/_Art, Materials | sonnet | unity-art-import |
| economy-balancer | simulate, adjust numbers | Configs, balance-targets.json | sonnet | unity-economy |
| qa-tester | tests, console, screenshots | reports only | sonnet | qa-harness |
| perf-auditor | draw calls, physics, allocs | reports only | sonnet | unity-perf-mobile |
| release-engineer | build config, checklist | build scripts, reports | sonnet | release-checklist |
| reviewer | read-only review vs house style | none | opus | unity-data-factory |

Frontmatter drafts (all `name`/`description` as shown; abbreviated descriptions are in the plugin when built):

```yaml
# orchestrator (main thread)
name: orchestrator
description: Runs the GDD-to-clone pipeline end to end. Use when the user supplies a GDD or asks to build, continue, or resume a game clone. Reads docs/agent-handoff.md first, delegates by phase, enforces iteration caps.
tools: Read, Write, Edit, Bash, Glob, Grep, Agent(game-designer, tech-lead, gameplay-dev, ui-dev, art-tech, economy-balancer, qa-tester, perf-auditor, release-engineer, reviewer)
model: opus
maxTurns: 80
memory: project
```
```yaml
# game-designer
tools: Read, Grep, Glob, Write, Edit
disallowedTools: Agent, Bash
model: sonnet
maxTurns: 30
skills: [game-designer-gdd]
memory: project
```
```yaml
# tech-lead
tools: Read, Grep, Glob, Write, Edit, Bash
disallowedTools: Agent
model: opus
maxTurns: 40
skills: [unity-data-factory]
memory: project
```
```yaml
# gameplay-dev
tools: Read, Edit, Write, Bash, Grep, Glob, mcp__unity-mcp__*
disallowedTools: Agent
model: sonnet
maxTurns: 60
skills: [unity-gameplay, unity-perf-mobile]
```
```yaml
# ui-dev
tools: Read, Edit, Write, Bash, Grep, Glob, mcp__unity-mcp__*
disallowedTools: Agent
model: sonnet
maxTurns: 60
skills: [unity-ui]
```
```yaml
# art-tech
tools: Read, Edit, Write, Bash, Grep, Glob, mcp__unity-mcp__*
disallowedTools: Agent
model: sonnet
maxTurns: 50
skills: [unity-art-import]
```
```yaml
# economy-balancer
tools: Read, Write, Edit, Bash, Grep, Glob
disallowedTools: Agent
model: sonnet
maxTurns: 50
skills: [unity-economy]
memory: project
```
```yaml
# qa-tester (does not edit code)
tools: Read, Bash, Grep, Glob, mcp__unity-mcp__*
disallowedTools: Edit, Write, Agent
model: sonnet
maxTurns: 40
skills: [qa-harness]
```
```yaml
# perf-auditor (reports only)
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, Agent
model: sonnet
maxTurns: 30
skills: [unity-perf-mobile]
```
```yaml
# release-engineer (never submits/uploads/commits/pushes without explicit approval)
tools: Read, Write, Bash, Grep, Glob
disallowedTools: Agent, Bash(git push *), Bash(git commit *)
model: sonnet
maxTurns: 30
skills: [release-checklist]
```
```yaml
# reviewer (read-only)
tools: Read, Grep, Glob
disallowedTools: Edit, Write, Bash, Agent
model: opus
maxTurns: 25
skills: [unity-data-factory]
```

`disallowedTools` entries such as `Bash(git push *)` use permission-rule syntax; the exact form in agent frontmatter is INFERRED. Test with one agent first.

---

## 5. Hook catalog

Hooks are the only enforcement (C23). Events/matchers VERIFIED (C15, C19); script logic INFERRED.

| ID | Event | Matcher | Action | Blocking | Purpose |
|---|---|---|---|---|---|
| H1 | SessionStart | `startup\|resume` | print `git status --short` + last 40 lines of `docs/agent-handoff.md` | no (context only, C17) | resume without prompt |
| H2 | PreToolUse | `Edit\|Write\|MultiEdit` | deny writes to protected paths | yes | keystores, signing, ProjectSettings, manifest |
| H3 | PreToolUse | `Edit\|Write` | deny hand-written `.unity/.prefab/.meta` | yes | AGENTS: never hand-author Unity YAML |
| H4 | PreToolUse | `Bash` + `if` | deny `git push`, `reset --hard`, `clean`, `checkout --`, `stash` | yes | AGENTS source-control rules |
| H5 | PostToolUse | `Edit\|Write` | on `.cs/.asset/.prefab/.unity` append path to `docs/pipeline/run-state/dirty.txt` | no | feeds Stop gate |
| H6 | Stop | none | if dirty non-empty run compile/test gate; exit 2 on red; loop cap | yes | compile + stop gate |
| H7 | PostToolUse | `Edit\|Write` on `**/SKILL.md` | run lint on that skill; exit 2 messages | feedback only | lint at write time |
| H8 | PreCompact | none | write phase + open tasks to handoff | no | survive compaction |
| H9 | Notification | none | desktop notification | no | interactive only |

Protected paths for H2 (INFERRED, owner to confirm): `**/*.keystore`, `**/*.jks`, `Upstore/**`, `**/google-services.json`, `**/*BounceConfig*.asset`; `ProjectSettings/**` and `Packages/manifest.json` (ask, not deny); `**/*.meta` (H3 covers content); `docs/feedback-notes.md`, `AGENTS.md` (append-only).

Compile/stop gate: preferred H6 as an `mcp_tool` hook (C20) calling the ivanmurzak Unity MCP compile/console tool (name must be discovered via `/mcp`). Fallback: `Unity.exe -batchmode -nographics -quit -projectPath <p> -logFile <f>` from a command hook; fails/hangs if the Editor already holds the project (INFERRED). Loop guard: the Stop-hook loop-protection input field was not found in the fetched reference (NOT READ); use a counter file `docs/pipeline/run-state/stop-gate.count`, max 3 blocks per phase, then write failure to handoff and allow stop; reset on pass.

settings.json snippet (structure VERIFIED C19-C22, paths INFERRED):

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume", "hooks": [
      { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/session_start.py\"", "timeout": 10 } ] }],
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit", "hooks": [
        { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/protect_files.py\"", "timeout": 5 },
        { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/no_handwritten_unity_yaml.py\"", "timeout": 5 } ] },
      { "matcher": "Bash", "hooks": [
        { "type": "command", "if": "Bash(git push *)", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/block_git_danger.py\"", "timeout": 5 },
        { "type": "command", "if": "Bash(git reset *)", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/block_git_danger.py\"", "timeout": 5 },
        { "type": "command", "if": "Bash(git clean *)", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/block_git_danger.py\"", "timeout": 5 } ] }
    ],
    "PostToolUse": [{ "matcher": "Edit|Write", "hooks": [
      { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/mark_dirty.py\"", "timeout": 5 },
      { "type": "command", "if": "Edit(**/SKILL.md)", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/lint_skills.py\" --one", "timeout": 10 } ] }],
    "Stop": [{ "hooks": [
      { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/stop_gate.py\"", "timeout": 900 } ] }],
    "PreCompact": [{ "hooks": [
      { "type": "command", "command": "py -I \"${CLAUDE_PROJECT_DIR}/tools/hooks/precompact_handoff.py\"", "timeout": 10 } ] }]
  }
}
```

Caveats (INFERRED): `if` with `Edit(...)` on PostToolUse is VERIFIED only for Bash; test it. On Windows confirm which shell runs hook commands before relying on `${CLAUDE_PROJECT_DIR}`. Test with `claude --debug`. For the plugin copy use `hooks/hooks.json` with `${CLAUDE_PLUGIN_ROOT}` (C22, C38).

---

## 6. Unattended local batch runner flow with iteration cap

Scope: a runner (self-hosted, Unity installed) runs the pipeline on a GDD and stops at a green gate or at caps. Human publishing never happens here.

Flags (names VERIFIED, values INFERRED):
```text
claude -p "$(cat prompts/run-pipeline.md)" --output-format json \
  --json-schema "$(cat tools/qa/run-result.schema.json)" \
  --permission-mode dontAsk --permission-prompts none \
  --allowedTools "Read,Edit,Write,Bash(py -I *),Bash(git status *),Bash(git diff *)" \
  --max-turns 60 --max-budget-usd 10 \
  --settings ci/settings.json --plugin-dir ./unity-game-pipeline
```
- Do not add `--bare` if hooks H1-H8 must run (C29 skips hooks). Whether `--settings` hooks run under bare is INFERRED; test. Bare needs `ANTHROPIC_API_KEY`; OAuth for local batch runner via `claude setup-token`.
- Pin the Claude Code version with `claude install <version>`.

Outer loop (cap lives outside the model):
```text
MAX_ITER=4  BUDGET_CAP=40 USD  TIMEOUT=45m
iter=1; session=""
loop:
  iter==1: claude -p <run prompt> ...   else: claude -p "Resume: fix failures in run-state/last-gate.json" --resume <session>
  session=out.session_id; spend+=out.total_cost_usd
  gate = py -I tools/qa/gate.py        # exit 0 only if all gates pass
  gate==0 -> GREEN; same signature as previous -> STUCK; spend>=BUDGET_CAP -> BUDGET; iter>=MAX_ITER -> CAP
write docs/agent-handoff.md (status, iterations, spend, failing gate, next human step); exit 0 iff GREEN
```
SIGTERM gives 143: treat as failed attempt, keep the handoff note. Budget is a client estimate; leave headroom.

gate.py GREEN means: (1) init event has no `plugin_errors`/`mcp_server_errors` (C31); (2) Unity compile zero errors; (3) EditMode tests pass (`-runTests -testPlatform EditMode`); (4) `lint_skills.py` exits 0 on changed skills; (5) `claude plugin eval <plugin> --json --threshold 0.8 --max-cost-usd 5 --trust-plugin` for changed hubs (threshold INFERRED); (6) screenshot QA for changed UI at three ratios; (7) no protected-path write attempts left unhandled.

Escalation: GREEN handoff states what shipped and what was not Editor-verified. STUCK/BUDGET/CAP: handoff lists failing gate, signature, last diff summary; a human decides. No retry beyond the cap.

---

## 7. Token playbook (VERIFIED unless marked)

1. Keep always-loaded instructions small: CLAUDE.md < 200 lines (C25); move Unity-specific rules into `.claude/rules/` with `paths:` (C26). The global instructions file is ~265 lines; trim it.
2. Heavy references behind lazy loading (C4).
3. Side-effect and rare skills manual with `disable-model-invocation: true` (C5).
4. Key use case first in each description, within 1,536 chars (C2).
5. Limit the listing: `"name-only"` overrides; avoid raising `skillListingBudgetFraction` (C3).
6. Subagents for research/log reading; short results; set `maxTurns` (C9, C13).
7. Preload only needed hubs (C10).
8. Keep MCP schemas deferred (C39); measure unity-mcp tool count first (INFERRED).
9. `--bare` in local batch runner for consistent start (C29) unless hooks are needed.
10. `--output-format json --json-schema` so the gate reads fields (C28).
11. Compact at phase boundaries and re-read the handoff; only the start of a skill survives compaction (C7).
12. Keep the prompt prefix stable; mid-session plugin changes can invalidate the cache (C40). Caching page NOT READ; verify with `total_cost_usd`.
13. Short explicit hook timeouts (5-10 s) (C21).
14. Numbers via `py -I` scripts, not reasoning in context (INFERRED).
15. Measure with `/doctor`, `/context`, and the `explain-usage` skill.

---

## 8. Risks

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 | Plugin rename breaks `/unity-ui` references | C6, C33 | choose prefix first; one-pass rename |
| R2 | Plugin subagents ignore permission mode / MCP config | C12 | put in project/local batch runner settings |
| R3 | 1,000 listed skills degrade routing | C3 | hubs + references; measure |
| R4 | `--bare` silently disables hooks | C29 | test `--settings` hooks; else drop `--bare` |
| R5 | Stop-gate loops forever | C16, no verified loop field | counter-file cap; handoff |
| R6 | Hooks run from untrusted repos in `-p` without trust dialog | headless | trusted checkouts only; keep secrets off runner |
| R7 | Batch compile fails while Editor holds the project | INFERRED | MCP compile in Stop hook; batch on idle runner |
| R8 | Hand-written Unity YAML corrupts scenes | AGENTS, catalog | H3 deny; Editor MCP only |
| R9 | Secrets in repo (keystores, google-services.json, default key literal) | pipeline-catalog risks (not re-checked) | H2 deny list |
| R10 | Auto memory / CLAUDE.md drift | C24, C27 | lint in gate; orchestrator rewrites handoff |
| R11 | Two agents write the same scene | AGENTS rule | one writer per scene; claims in handoff |
| R12 | Plugin eval gated by kill switch and costs money | embedded ref | optional in gate; cap cost; exit 2 = partial |
| R13 | `/skill-doctor`, `plugin eval` availability varies | embedded ref | check at local batch runner start |
| R14 | `sync.ps1` in memory does not exist | repo listing | fix memory note or create it |
| R15 | Subagent frontmatter typos silently ignored | C1, C9 | L3 applies to agents too |
| R16 | Hook `if` syntax for non-Bash tools unverified | section 5 | test H7 first |

## 9. Open questions

1. Skill prefix: bare names or plugin namespace?
2. local batch runner permission model: `dontAsk` + allow list (proposed) or `auto` with `--permission-prompts none`?
3. Exact unity-mcp compile tool name for the Stop hook (needs live `/mcp`).
4. Do `--settings` hooks run under `--bare`?
5. Protected-path list; `Packages/manifest.json` deny vs ask.
6. Iteration caps (4 attempts, USD 40) are placeholders.

---

## 10. Proposed classification

| Type | Proposed name | What it is | Must-haves |
|---|---|---|---|
| RULE | `house-style-core` | short always-loaded CLAUDE.md distilled from AGENTS.md + global file | < 200 lines; reason per rule; points to path rules; no skill duplication |
| RULE | `safety-no-handwritten-unity-yaml` | never author .unity/.prefab/.meta by hand | enforced by H3; reason stated; deny message names the MCP path |
| RULE | `safety-protected-paths` | keystores, ProjectSettings, manifest, claims | enforced by H2; ask-vs-deny list; owner-editable |
| RULE | `workflow-never-overwrite-newer-work` | re-read before edit; one writer per scene | handoff append protocol; claim check; merge-or-ask |
| RULE | `mobile-low-end-defaults` | path rule for Assets/_Game/Scripts/** | collision registry, pooling, no per-frame alloc, no PC settings on mobile tier |
| SKILL | `pipeline-router` | entry hub: GDD intake, phases, resume | reads handoff first; delegates; ends with handoff write |
| SKILL | `unity-ui` | existing UI hub | sharp description; popup/tabs/list/toast references; idempotent builder; screenshot QA |
| SKILL | `unity-data-factory` | DataBlock, Factory, StaticBus, configs | framework version check; no invented APIs; wiring checklist |
| SKILL | `unity-gameplay` | controller, camera, platforms, checkpoints, bots | feel table defaults; collision registry; recipe per actor |
| SKILL | `unity-economy` | daily, jackpot, gacha, restock, IAP/ads | odds are an owner decision; balance loop with stop criteria; simulation script call |
| SKILL | `release-checklist` | build + compliance checks | manual-only; never submit without approval; secrets check |
| RECIPE | `ui-popup-anatomy` | Popup Root > Scale > Board > Btn_Close, OutBack tween | exact hierarchy; tween timing; close-button rule; reference path |
| RECIPE | `economy-daily-reward` | daily reward data, factory, UI, claim flow | data record, config asset, factory entry, event, wiring steps |
| RECIPE | `gameplay-minigame-scaffold` | new minigame: registration, state, scoring, exit | factory registration; state machine owner/state; cleanup on exit |
| TOOL | `lint_skills.py` | skill + agent lint | rules L1-L13; exit codes; `--one` mode; no network |
| TOOL | `hooks/` set | H1-H9 scripts + hooks.json | exit 2 on deny; timeouts; logs to run-state; tested with fake event |
| TOOL | `tools/qa/gate.py` + `run_pipeline` | outer loop, gates, handoff writer | iteration + budget caps; signature check; GREEN/STUCK/BUDGET/CAP |
| TOOL | `agents/*.md` roster | eleven subagent definitions | least-privilege tools; disallowedTools for leaves; preload only hubs |
| TOOL | Unity editor batch scripts | compile, EditMode run, screenshots at 3 ratios | idempotent; JSON output; no scene save without claim; idle Editor only |
| DATA | `docs/agent-handoff.md` | resume state | date, agent, files, next step; append-only |
| DATA | `docs/pipeline/gdd.yaml` | normalized GDD input | versioned schema; each feature has source quote + acceptance check |
| DATA | `docs/pipeline/balance-targets.json` | numeric targets + tolerances | target, tolerance, cap; owner field; reasoned changes only |
| DATA | `docs/pipeline/run-state/` | dirty list, gate result, counters | written by hooks/gate only; reset per phase; not committed by default |
