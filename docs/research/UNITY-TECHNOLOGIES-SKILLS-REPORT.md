# Unity-Technologies/skills review (2026-11-02)

Reference clone (read-only, untrusted): C:\Unity\GitProject\_skill-research\Unity-Technologies-skills (34 skills).

## Licence notes
LICENSE.md states "Unity Skills (c) 2026 Unity Technologies, licensed under the Unity Companion License for Unity-dependent projects", provided AS IS. The full UCL text is only linked (unity3d.com/legal/licenses/unity_companion_license), not included, so exact terms were NOT verified here. Conservative handling: no text or code was copied; every new skill is a fresh, shorter rewrite in our wording, with a `Source: official (Unity-Technologies/skills/<name>)` line and our additions marked `[ours]`. Do not copy the reference repo files into our repo. Owner should read the UCL if verbatim reuse is ever wanted.

## Verdicts
| Reference skill | Verdict | Ours |
|---|---|---|
| optimize-text-mesh-pro | ADDED | tmp-font-optimization |
| manage-sprite-atlas | ADDED | sprite-atlas-v2 |
| optimize-audio + audio-setup-mixers | ADDED | audio-import-and-mixer-optimization |
| urp-postprocessing | ADDED | urp-postprocessing-volumes |
| validate-urp-render-graph-renderer-feature | ADDED | urp-renderer-feature-review |
| migrate-birp-to-urp | ADDED | birp-to-urp-migration (+ references/phases.md) |
| physics-3d-collision | ADDED | physics-callback-troubleshooting |
| project-auditor-fixes | ADDED | project-auditor-triage |
| initialize-ai-navigation | ADDED | ai-navigation-setup |
| ui-ugui | IMPROVED | unity-ui (layout group / CanvasScaler rules) |
| implement-in-app-purchases | IMPROVED | iap-catalog (IAP 5 flow, two-step confirm) |
| localization | IMPROVED | localization-pipeline |
| unity-pipeline, unity-cli (editor-control gotchas) | IMPROVED | unity-mcp-workflow (CLI itself INCOMPATIBLE: we use MCP) |
| optimize-* cross refs | IMPROVED | mobile-perf-audit |
| ui (router) | DUPLICATE | ui-always |
| new-unity-project | DUPLICATE | unity-project-bootstrap, new-game-bootstrap |
| craft-game-floors | DUPLICATE | game-feel-polish, done-means-wired, gate-check |
| unity-package-management | DUPLICATE | unity-mcp-workflow, house-style-foundation (package rules) |
| generate-editor-search-query | SKIPPED | editor-only convenience, low value |
| 2d-pixel-perfect, create-2d-physics, create-tile-palette-or-rule-tiles, sprite-editor, sprite-segment-3x3grid | SKIPPED | our games are 3D mobile, not 2D pixel art |
| ui-uitk, ui-imgui | SKIPPED | runtime UI is uGUI; revisit for Editor tools only |
| shader-graph-create-custom-node | SKIPPED | we hand-write URP shaders |
| optimize-web | SKIPPED | no WebGL target |
| setup-multiplayer-services, setup-vivox-voice-chat, build-live-game | SKIPPED | single-player, no UGS/voice |
| levelplay-unity-integration | SKIPPED | our ads go through the project SDK wrapper (`ads-layer-generic`) |
| build-gtk | SKIPPED | not relevant to our projects |
| asset-transformer-toolkit | INCOMPATIBLE | needs com.unity.industry.toolkit and Pixyz licence |

Counts: ADDED 9, IMPROVED 5 (unity-ui, iap-catalog, localization-pipeline, unity-mcp-workflow, mobile-perf-audit), DUPLICATE 4, SKIPPED 15, INCOMPATIBLE 1 (plus unity-cli noted incompatible in the IMPROVED row). Not read in full: levelplay, build-gtk, ui-uitk, ui-imgui, optimize-web, setup-*, sprite-* (verdicts from name, description and headings only).

## Notes
- Reference skills carry anti-patterns we avoid: interactive "ask the user" gates (we decide, log, continue), "must end with an AnswerBlock", and manual-menu atlas scripts.
- Review angle: facts are from the reference text at clone time; Unity 6.3 API names (Render Graph, IAP 5, TMP 3.2 preview) should be re-checked against the installed package source before use.
