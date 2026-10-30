# Skill process retro (2026-10-30): why skills were not applied automatically

Evidence (one long vibe-coding session):
1. The prompt router hook had a PowerShell parse error (non-ASCII literals in a BOM-less file under PowerShell 5.1), so it injected nothing for most of the session. Fixed: ASCII-only scripts, parse check in `sync_claude_setup.ps1`.
2. Even with hints, the model skipped them: hints were advisory and nothing verified compliance (UI edits shipped with no measurement; screenshots with misaligned text were not acted on).
3. The measurement the skills demand was manual (a hand-written script each time), so it was skipped. No Qa tool existed although the instructions named some.
4. Subagents never saw the skills (one admitted it read only `ui-always`); briefs depended on the coordinator remembering.
5. Rules grew as prose in a 330+ line AGENTS.md (low salience); some skills were game-specific (not reusable).
Fixes: data-driven router over every skill (`skill_router.json`), plan/screenshot/test/console observation hooks (`skill_observe_hook.ps1`), enforcement gate on Stop/SubagentStop + SubagentStart contract (`skill_enforce_hook.ps1`), portable `ui-layout-audit` tool skill, neighbour-gap/padding/outline rules in the UI skills, project-agnostic skills only.
Rule of thumb: if a rule matters, give it a tool that measures it and a hook that blocks without it.
