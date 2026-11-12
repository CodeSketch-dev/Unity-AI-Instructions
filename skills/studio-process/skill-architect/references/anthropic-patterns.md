# Patterns learned from anthropics/skills (reference only, nothing copied)

Repo: github.com/anthropics/skills (Apache-2.0 for most, check each folder's license). Do NOT clone it. Fetch one file when needed:
`https://raw.githubusercontent.com/anthropics/skills/main/skills/<name>/SKILL.md`. Read-only; never edit vendor skills.

## Which vendor example to read for what
- Making or improving any skill, evals, description tuning: `skill-creator` (also installed here as `anthropic-skills:skill-creator`).
- Tool/server generation with phases and reference files: `mcp-builder`.
- Script-heavy skills with a helper CLI: `pdf`, `xlsx`, `docx`, `pptx`.
- Starting point: `template/` folder of the repo (name + description only).

## Ideas adopted into this studio
- The description is the trigger: put every "when" in it, make it a bit assertive (models undertrigger), cover near-miss contexts.
- Explain the why of a rule instead of shouting in caps; write general guidance, not fixes for one test prompt.
- Test = 2-3 realistic prompts, each run with the skill and with a baseline (no skill, or the old version); grade assertions; look at transcripts for wasted steps; bundle a helper script when every run reinvents it.
- Trigger tuning = ~20 queries, half should-fire and half near-miss, hold out a test split, pick the description by held-out score. Local offline version: `scripts/trigger_eval.py` (router simulation, no model call); the model-based loop is `anthropic-skills:skill-creator` description optimisation.
- Keep SKILL.md lean; move long material to `references/`; scripts for deterministic work.

## Not adopted
Packaging to `.skill` files and the HTML eval viewer: this studio syncs skills with `sync.bat`/`publish.bat`.
