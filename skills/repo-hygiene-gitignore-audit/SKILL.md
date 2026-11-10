---
name: repo-hygiene-gitignore-audit
description: "Find first-party Unity files silently hidden from git AND derived/generated folders wrongly tracked (template globs like Demo*, tool indexes inside Assets, screenshots) so a fresh clone compiles and the repo stays lean. Use before milestones or after adding a feature folder."
triggers: gitignore, ignored folder, tracked generated folder, derived folder, untracked, fresh clone, clone does not compile, missing script, folder not committed, git check-ignore, khong commit duoc, thieu file, clone moi loi
---

# Repo hygiene: gitignore audit
A Unity template `.gitignore` often has broad patterns (`Assets/**/Demo*`, `Tutorial*`, `Sample*`, `Example*`). They silently hide first-party folders whose names merely START with those words (a `Demo` feel-layer folder, `Demolition`, a pet named `DemonKing`). The working tree still compiles, the repo does not.

## Audit (run at every milestone, 10 seconds)
1. `git status --short --ignored <first-party root> | grep '^!!' | grep -v '\.omc'` : every hit must be intentional (Library-like, generated). A source folder or `.meta` here is a bug.
2. `git ls-files --others --exclude-standard <first-party root> Assets/Resources ProjectSettings Packages` : untracked files that are NOT ignored: singleton ScriptableObjects (`Resources/.../Factory_*.asset`), new tests' `.meta`, baked assets. Each one missing from the repo breaks a fresh clone at runtime (not at compile).
3. For a hit: `git check-ignore -v <path>` shows the rule; add negations AFTER the rule: `!Assets/_Game/Scripts/Logic/<Feature>/Demo/` plus its `.meta`; then `git add` and commit separately with the reason.
4. When naming a new folder or asset, avoid template words as prefixes (Demo, Tutorial, Sample, Example, Test) or add the negation in the same commit.

## Reverse audit: tracked files that should not be
1. `git ls-files Assets | grep -iE 'graph|cache|generated~|backup~|__pycache__|\.tmp'` and `git ls-files | grep -E '^Assets/[^/]+\.(png|jpg)$'` : derived tool output, screenshots and backups inside `Assets/` are imported by Unity on every refresh and bloat the pack. Untrack with `git rm -r --cached <folder>`, add the ignore rule (not only a root-anchored one: `/Assets/<folder>/` and its `.meta`), prove with `git check-ignore -v`, commit alone. Keep the files on disk for the tool that writes them, or move the tool output outside `Assets/`.
2. `git count-objects -vH` for the pack size, `lean-asset-audit/scripts/size_report.py` for tracked suspects and text-serialized giants. A history rewrite is the owner's decision, never run.
3. Write sizes down before and after (`staged-refactor-playbook` lean table).

## Rules of a good Unity `.gitignore`
- Ignore: Library, Temp, Obj, Build(s), Logs, UserSettings, MemoryCaptures, IDE folders, `*.csproj`/`*.sln`/`*.slnx`, apk/aab, generated Addressables binaries, the screenshot/report output folders of your Editor tools, generated skill/agent copies.
- Always track `.meta` (`!/Assets/**/*.meta`), `Packages/manifest.json`, `packages-lock.json` and `ProjectSettings/ProjectVersion.txt` (ignoring the version file breaks reproducible Editor pinning).
- Asset Store junk globs under `Assets/**` (`Demo*`, `Example*`, `Sample*`, `Tutorial*`, `Document*`) are the main source of silent loss; anchor them to vendor folders instead of `Assets/**`, or negate first-party paths explicitly. A missing tutorial hand sprite once vanished from a clean clone because of such a glob.
- Verify every new generated folder and every new feature folder with `git check-ignore -v <file>`.
- Commit-level conventions (message format, tags, generated-file policy): `git-hygiene-conventions`.

## Private studio files never reach teammates
- `sync.bat` keeps the studio skills local: `.claude/` (skills, ai-instructions copy), `CLAUDE.local.md` (the managed block lives here, not in the shared `CLAUDE.md`) and `Assets/_AiQa/` are ignored. Teammates get a clean repo; only machines that cloned the AI-Instructions repo and ran `sync.bat` load the skills.
- Two idempotent writers, both from `tools/sync_claude_setup.ps1`: (1) the Unity project's own `.gitignore` gets only the MISSING private lines appended (never rewritten); (2) the git ROOT `.gitignore` (or `.git/info/exclude` when root == Unity folder) gets a marker-delimited block (tool output, scratch/backup folders, generated docs subfolders and media). Rerunning replaces the block, no duplicates.
- Ignore rules do not untrack: a file already committed stays tracked until `git rm --cached`. After sync, `git status` may show `CLAUDE.md` modified (old block stripped): review it, never commit private files.

## Also
- Subagent output is only real once committed: after a batch, `git status` and compare with the files the agent reported.
- A green local EditMode run proves nothing about a clean clone; if time allows, `git clone` to a temp dir and diff `git ls-files` against the working tree.
