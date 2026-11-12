# Repo Restructure + Lint-Triggered Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native, one writer, shared hook paths) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Give this skills repo a clean, enforced layout and a Lint-Triggered Skills mechanism, so any agent (Claude Code, Codex, subagents) that edits skills, hooks or Unity C# is pushed by a linter to the exact skill it must read.

**Architecture:** (1) `tools/publish/repo_layout_lint.py` encodes the target layout as a failing-first test, then files move with `git mv` until it passes; `publish.ps1` runs it so a messy layout can never be published. (2) A local rule engine `tools/lint/` (Python, stdlib only): one file per rule, each message is a micro-prompt naming the skill file to read; a PostToolUse hook runs it only on the edited file. (3) Meta-skill `capture-pattern-with-lint` turns "save this lesson" into skill + rule + test. (4) An authoring standard (doc + hook injection + lint) makes every other agent follow the same flow.

**Tech Stack:** Python 3 stdlib (lint, tests via `unittest`/`pytest` as in `tools/tests/`), PowerShell 5.1 hooks (ASCII only), `sync.bat`, `publish.bat`.

**Spec:** user messages 2026-11-12 (Lint-Triggered Skills request + "full restructure" + "other agents must follow the standard: guidance, automatic, tools/lint"). Recorded as OR-001..OR-003 in `docs/owner-requests.md`.

## Global Constraints

- Installed hook contract is FLAT: `settings.json` holds 14 commands pointing at `%USERPROFILE%\.claude\pipeline-hooks\hooks\<name>.ps1`. File names and that flat install location must not change.
- `hooks/hooks.json` + `hooks/scripts/*.py` are a Claude plugin (`${CLAUDE_PLUGIN_ROOT}/hooks/scripts/...`): do not move or rename `hooks/scripts/`.
- Hook `.ps1` files are ASCII only (PowerShell 5.1); `sync_claude_setup.ps1` parse-checks them.
- Skill folder names are not renamed (305 folders, referenced by name everywhere).
- English for all files. No commits to Unity projects from this repo. No `git reset --hard`/clean. Publish only via `publish.bat`.
- Lint messages name the skill path as it exists INSIDE the target Unity project: `.claude/skills/<name>/SKILL.md` (sync installs skills there; Codex reads the same file via its terminal tool). Never a repo-relative `skills/...` path in a message. One engine, one message format for Claude Code and Codex: no per-platform config.
- Zero startup context: lint skills are NOT added to always-on text (AGENTS.md, digest). Only the linter output loads them, at the moment of violation. Rule messages stay under ~300 chars.
- `skills/INDEX.md`, `skill_router.json` are generated files; never hand-edit.

## Review Focus

1. Installed `pipeline-hooks\hooks\` is a stale full mirror of the old repo root; after the move the flat `.ps1`/`.json` must still land there (else every hook silently dies).
2. A second machine pulls the restructure while still running old `sync.bat`: `publish.ps1` pull must not break it (sync.bat and its hook list change in the same commit).
3. Lint false positives block agents forever: a rule needs an opt-out comment and path scoping (Editor/ and Tests/ excluded).
4. Hook crash must never block edits: lint hook exits 0 when Python is missing or the rule engine raises.
5. Windows paths with spaces (`Code Sketch`) in hook commands and in `git mv`.

---

## File Structure (target)

```
/ AGENTS.md  README.txt  STUDIO-BRAIN-DIGEST.md  publish.bat  sync.bat  data/projects.txt   (only these files at root)
skills/ agents/ commands/ data/templates/ tools/evals/ docs/ tools/ tools/packages/
hooks/ hooks.json  scripts/ (plugin py, unchanged)  ps1/ (9 moved hook scripts)
data/  skill_router.json  studio_rules.json
tools/lint/  engine.py  run_lint.py  rules/*.py  tests/
.local/ (gitignored: .publish-backup, .skill-loop, outputs)
```

`.superpowers` and `.claude-plugin` stay (tool-owned dot folders).

### Task 1: Layout lint (RED first)

**Files:** Create `tools/publish/repo_layout_lint.py`, `tools/tests/test_repo_layout_lint.py`

**Interfaces:**
- Produces: `check_layout(repo: Path) -> list[str]` (violation messages, each names the fix and `docs/REPO-LAYOUT.md`); CLI `python tools/publish/repo_layout_lint.py [repo]` exits 1 on violations.

- [ ] **Step 1: Write failing tests** `test_root_only_allows_listed_files`, `test_stray_ps1_at_root_is_flagged`, `test_data_json_must_live_in_data`, `test_clean_tree_passes` (tmp_path fixtures, assert messages contain `docs/REPO-LAYOUT.md`).
- [ ] **Step 2:** `python -m pytest tools/tests/test_repo_layout_lint.py -q` expect FAIL (module missing).
- [ ] **Step 3:** Implement `check_layout` with root allowlist (files above, dirs above, dot-dirs `.git .claude-plugin .superpowers .local`), skill-folder rule (each `skills/<n>/` has `SKILL.md`).
- [ ] **Step 4:** Run tests, expect PASS. Run CLI on the real repo, expect FAIL listing the 9 `.ps1` + 2 `.json` + 3 dirs (this is the RED baseline for Task 2).

### Task 2: Move files, repoint every reference

**Files:** `git mv` the 9 ps1 to `hooks/ps1/`, 2 json to `data/`, 3 runtime dirs to `.local/`; Modify `sync.bat`, `tools/sync/sync_claude_setup.ps1`, `tools/skillkit/build_skill_router.py` (default out path), `tools/publish/publish.ps1`, `.gitignore`, the 4 `$PSScriptRoot` data lookups in `hooks/ps1/*.ps1` (fallback `..\..\data`), `AGENTS.md` mentions.

**Interfaces:** Consumes Task 1 CLI. Produces: `sync.bat` step "flatten": copy `hooks\ps1\*.ps1` and `data\*.json` into `%CLAUDE_HOME%\pipeline-hooks\hooks\` (flat), then parse-check.

- [ ] **Step 1:** Snapshot evidence: `Get-FileHash` of installed flat files and `settings.json` hook command list saved to `.local/pre-restructure.txt`.
- [ ] **Step 2:** `git mv` files; update references listed above (grep each old name; expect zero stale hits outside docs history).
- [ ] **Step 3:** `python tools/publish/repo_layout_lint.py` expect PASS; `python tools/skillkit/build_skill_router.py skills data/skill_router.json` expect same skill count as before.
- [ ] **Step 4:** `sync.bat /nopause /nopull /nopro` expect exit 0, flat installed hooks present and parse-clean; pipe a fake prompt JSON into the installed `ui_gate_reminder.ps1` and expect the Skill router line.
- [ ] **Step 5:** Run `tools/tests` full suite; compare pass/skip counts to a pre-move run recorded in Step 1.

### Task 3: Rule engine (Lint-Triggered Skills core)

**Files:** Create `tools/lint/engine.py`, `tools/lint/run_lint.py`, `tools/lint/rules/__init__.py`, `tools/lint/tests/test_engine.py`

**Interfaces:**
- Produces: `@dataclass Rule(id, pattern, why, skill, paths=("**/*.cs",), exclude=("**/Editor/**","**/Tests/**"))`; `lint_text(path: str, text: str) -> list[Violation]`; message format `[RULE <id>] <why> MANDATORY: read .claude/skills/<skill>/SKILL.md before fixing this line. (line N) Opt out only with // lint-ok:<id> <reason>`. CLI `run_lint.py <file>...` prints violations, exit 2 if any (hook contract), exit 0 on engine error.

- [ ] **Step 1:** Failing tests: match yields message with skill path; `lint-ok:<id>` suppresses; excluded Editor path ignored; unknown file type ignored; engine exception returns 0.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement. **Step 4:** Run, expect PASS.

### Task 4: PostToolUse hook, installed by sync

**Files:** Create `hooks/ps1/lint_on_edit.ps1`; Modify `tools/sync/sync_claude_setup.ps1` (register `PostToolUse` matcher `Edit|Write|MultiEdit`, same pattern as the ink hook); `hooks/hooks.json` (plugin entry).

**Interfaces:** Consumes `tools/lint/run_lint.py`. Hook reads tool JSON from stdin, takes `tool_input.file_path`, runs lint on that one file, writes violations to stderr, exit 2.

**Per-project install (owner confirmed: agents only work well after sync into the Unity project):** `sync_claude_setup.ps1` also copies `tools/lint/` to `<project>\.claude\lint\` and writes the PostToolUse hook into the project's `.claude\settings.json` (idempotent, command uses a project-relative path so it survives other machines). Codex in that project runs `python .claude/lint/run_lint.py <file>` (documented in the project `.claude/ai-instructions.md` block and the hub preamble). Skills already land in `<project>\.claude\skills`, matching the message path.

**Same behaviour for Claude and Codex:** rules live once in `tools/lint/rules/` and are synced into every project like skills (new rule = next sync, no per-agent config). Claude gets it per edit via the hook; Codex has no hooks, so `run_lint.py --changed` lints every file in `git status` of the project and is required by the hub preamble before reporting done. Both print the identical micro-prompt (`.claude/skills/<name>/SKILL.md`). Test: same bad fixture, hook path and `--changed` path emit byte-identical messages.

**Git hygiene:** the managed ignore block that sync already writes ignores `/.claude/` (and `.agents/`, `CLAUDE.local.md`), so `.claude/lint/` and the project hook settings never reach the Unity repo. Verify per project with `git check-ignore -v .claude/lint/run_lint.py`; if a project already TRACKS `.claude/` files, report them (do not untrack automatically).

- [ ] **Step 1:** Test: pipe `{"tool_input":{"file_path":"<fixture .cs with new GameObject>"}}` to the hook, expect exit 2 and the micro-prompt on stderr; non-`.cs` file expect exit 0 and no output.
- [ ] **Step 2:** Implement hook (ASCII, 5 s budget, `python` missing -> exit 0). **Step 3:** register in sync; run sync; expect `settings.json` contains exactly one lint hook entry (idempotent on second run).

### Task 5: Sample skill + rule

**Files:** Create `skills/no-runtime-manager-gameobject/SKILL.md`, `tools/lint/rules/no_runtime_manager_gameobject.py`, `tools/lint/tests/fixtures/bad_manager.cs`, `tools/lint/tests/fixtures/good_manager.cs`

Convention chosen: managers/world pieces are scene-authored prefabs, never `new GameObject(...)`/`AddComponent` at runtime (AGENTS.md "Scene-authored prefabs", skill `scene-authored-prefabs`). Pattern: `new\s+GameObject\s*\(` combined with `AddComponent<`/`DontDestroyOnLoad` in the same file; the skill is a 30-line fix recipe pointing at `scene-authored-prefabs` and `persistent-root-prefab`.

- [ ] **Step 1:** Fixture tests: bad file flagged at the right line, good file clean, opt-out works. **Step 2:** expect FAIL. **Step 3:** write rule + skill. **Step 4:** expect PASS and run `skill_lint.py` on the new skill, expect 0 errors.

### Task 6: Meta-skill `capture-pattern-with-lint`

**Files:** Create `skills/capture-pattern-with-lint/SKILL.md`; Modify `skills/studio-hook-factory/SKILL.md` (cross-link), `data/studio_rules.json` (inject the 3-step flow when the owner says "save this pattern / learn from this mistake / rut kinh nghiem").

Content: Step 1 write short skill (frontmatter, `Use when`, triggers incl. Vietnamese without accents); Step 2 write `tools/lint/rules/<id>.py` + fixtures pointing at that skill; Step 3 run `python -m pytest tools/lint/tests -q`, then run the linter on a bad fixture and show the micro-prompt; Step 4 `publish.bat`. Includes the micro-prompt message template and the false-positive checklist (Review Focus 3).

- [ ] **Step 1:** write skill; **Step 2:** `skill_lint.py` 0 errors; **Step 3:** router build, then `skill_route.ps1 "save this pattern as a lint rule"` expect the skill in output.

### Task 7: Authoring standard for every agent (automatic)

**Files:** Create `docs/REPO-LAYOUT.md` (where each kind of file goes, how to add a skill, hook, rule, data file); Modify `AGENTS.md` (short always-on rule: layout + "new reusable lesson = skill + lint rule"), `STUDIO-BRAIN-DIGEST.md` (one line), `data/studio_rules.json` (PreToolUse-style injection when a path under this repo is edited), `tools/publish/publish.ps1` (run `repo_layout_lint.py` and `python -m pytest tools/lint/tests -q`; abort publish on failure), `tools/skillkit/skill_lint.py` (warn when a skill says "never/always use X" for a code pattern but no `tools/lint/rules/*` references it: advisory).

Foundation promotion verdict: yes — enforced by publish gate, rules injection and PostToolUse lint.

- [ ] **Step 1:** Failing test: `test_publish_gate_blocks_layout_violation` (tmp repo with stray root `.ps1`, expect nonzero from the gate function). **Step 2:** FAIL. **Step 3:** wire publish + docs + rules. **Step 4:** PASS.

### Task 8: Verify and publish

- [ ] Run: layout lint PASS, `tools/lint/tests` PASS, `tools/tests` pass/skip counts equal to Task 2 baseline, `sync.bat` exit 0, installed hook smoke (prompt router + lint hook) works from the flat location.
- [ ] Invoke superpowers:requesting-code-review on the diff; fix findings; superpowers:verification-before-completion.
- [ ] `publish.bat "Restructure repo layout; add lint-triggered skills; foundation yes"` (background, read output). Exit 2 = merge per conflict rule.

## Self-Review

Spec coverage: item 1 (inspect + PostToolUse) Tasks 2-4; item 2 (rule structure + micro-prompt) Task 3; item 3 (meta-skill) Task 6; item 4 (sample) Task 5; restructure Tasks 1-2; "other agents must follow" Task 7. Type consistency: `Rule`/`Violation`/`lint_text`/`check_layout` names used identically across tasks. Proportion: plan stays signatures + assertions, no function bodies.
