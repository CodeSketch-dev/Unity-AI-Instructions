---
name: repo-hygiene-gitignore-audit
description: "Find first-party Unity files silently hidden from git (template .gitignore patterns like Demo*, Tutorial*, Sample*, singleton assets never added) so a fresh clone compiles. Use before pushing milestones, after adding a feature folder, or when a push 'works here' only."
triggers: gitignore, ignored folder, untracked, fresh clone, clone does not compile, missing script, folder not committed, git check-ignore, khong commit duoc, thieu file, clone moi loi
---

# Repo hygiene: gitignore audit
A Unity template `.gitignore` often has broad patterns (`Assets/**/Demo*`, `Tutorial*`, `Sample*`, `Example*`). They silently hide first-party folders whose names merely START with those words (a `Demo` feel-layer folder, `Demolition`, a pet named `DemonKing`). The working tree still compiles, the repo does not.

## Audit (run at every milestone, 10 seconds)
1. `git status --short --ignored <first-party root> | grep '^!!' | grep -v '\.omc'` : every hit must be intentional (Library-like, generated). A source folder or `.meta` here is a bug.
2. `git ls-files --others --exclude-standard <first-party root> Assets/Resources ProjectSettings Packages` : untracked files that are NOT ignored: singleton ScriptableObjects (`Resources/.../Factory_*.asset`), new tests' `.meta`, baked assets. Each one missing from the repo breaks a fresh clone at runtime (not at compile).
3. For a hit: `git check-ignore -v <path>` shows the rule; add negations AFTER the rule: `!Assets/_Game/Scripts/Logic/<Feature>/Demo/` plus its `.meta`; then `git add` and commit separately with the reason.
4. When naming a new folder or asset, avoid template words as prefixes (Demo, Tutorial, Sample, Example, Test) or add the negation in the same commit.

## Also
- Subagent output is only real once committed: after a batch, `git status` and compare with the files the agent reported.
- A green local EditMode run proves nothing about a clean clone; if time allows, `git clone` to a temp dir and diff `git ls-files` against the working tree.
