# AGENTS.md changelog (project file only)

Merge edits, not overrides: user intent kept, wording aligned with mined practice. Source = pipeline-catalog "Contradictions" list. Global `~/.claude/CLAUDE.md` is NOT touched; it copies AGENTS.md via `sync.bat` when the user runs it.

## 2026-10-15
| # | Section | Change | Why / source |
|---|---|---|---|
| 1 | Framework selection | CodeSketch and SketchEngine described as one framework, v1/v2 | catalog contradiction 2, report 01 |
| 2 | Tween library | "prefer PrimeTween for new code"; note both ship side by side | contradiction 5 |
| 3 | Mobile performance, static reset | note that framework collision maps and older zones don't reset yet | contradiction 7 |
| 4 | Mobile performance, URP baseline | runtime device policy instead of many Quality levels; reference Mobile asset is looser than baseline | contradiction 3 |
| 5 | Mobile performance | added 60 fps cap line | contradiction 4 |
| 6 | Mobile performance, pooling | `PoolPrefabGlobal`/`PoolPrefabConfig`/`Pool_Manager`; LeanPool only if already used | contradiction 1, report 03 |
| 7 | Mobile performance, materials | one-material goal with per-family fallback; OmniShade for skins; SRP Batcher compatible | contradictions 6 and 10, user decision |

Not edited (need role split or user call first): contradiction 8 (StaticBus pairing breach is code, not wording), contradiction 9 (icon vs button ratio belongs to `ui-style-rules`).
