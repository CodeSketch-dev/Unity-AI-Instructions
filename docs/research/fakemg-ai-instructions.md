# Research note: FakeMG/ai-instructions (read 2026-11-12, public repo, owner's friend)

Source: github.com/FakeMG/ai-instructions (29 files: skills/shared, instructions/shared, prompts, unity/, general-coding/, merge.ps1). Read via the GitHub tree API + raw files; nothing executed or copied verbatim. The profile has 26 repos; only this one is about AI instructions (`FakeMGFramework` is a C# framework, not read).

## Taken (distilled into our generic skills, own words)
| Source skill | Our skill | What we kept |
|---|---|---|
| lcom4 | `lcom4-cohesion-check` (new) | deterministic split metric, exclusions, special cases, output |
| intent-clarifier | `intent-clarifier` (new, invite-only) | Intent Document + round protocol; adapted to our "decide and record a Ruling" default |
| reviewing-tests, unity-testing | `unity-test-quality-review` (new) | 8-question checklist, five categories, EditMode vs PlayMode |
| multi-agent-review | `parallel-qa-fanout` (section) | one agent per criterion, lossless merge, coverage check |
| game-juice | `game-feel-polish` (section) | numeric guardrails not yet in our skill |
| architecturing-game-feature | `spec-then-plan` (section) | tradeoffs one at a time, interface only with 2+ implementations, skeleton output |

## Not taken (and why)
- VContainer / NSubstitute specifics: our projects use SketchEngine patterns; noted as project-level choice.
- `merge.ps1` (merge instruction files from GitHub into one markdown): our `sync.bat` + publish already install AGENTS.md and skills into Claude, Codex and projects.
- unity-mcp-orchestrator references (60-75 KB): we already have `unity-mcp-workflow` for the `ivanmurzak` server; the references target a different MCP.
- coding-convention / personas / unity-techstack: overlap our house style; not read in detail (candidate for a later diff pass).

## Idea worth a later look
- Per-skill `agents/openai.yaml` stubs next to SKILL.md for Codex discovery.
