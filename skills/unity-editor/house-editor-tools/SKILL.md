---
name: house-editor-tools
description: "Use when a new or refactored Unity project needs the standard Editor tool kit: scene optimizer bake, data reset and hotkeys, QA ink loop, prefab replace, material and collider tools, audio config and glyph tools, plus tests asmdefs, build/version method, pre-commit missing-reference check and CI."
triggers: editor tool, editor tools, menu item, bootstrap kit, tool kit, scene optimizer, bake all, clear data menu, hotkeys, prefab replace, collider extractor, material collector, audio config generator, glyph preloader, ink audit, pre-commit, missing reference check, ci, build method, version bump, cong cu editor, bo cong cu, kiem tra truoc commit
---

# House editor tools (ranked bootstrap kit)

Why: the daily speed of a one-person studio comes from small, boring Editor tools: one hotkey bakes the scene, one menu wipes the save, one batch method proves nothing is broken. This skill lists what to install in a new project, in rank order, with the safety rules every tool must follow, and the four things the reference project lacks (tests, build method, pre-commit check, CI).

## 1. Rules for every tool (`editor-tool-authoring`, `rule-editor-tool-safety`)
- Idempotent: a second run changes nothing (verify with `git status`). Chunked, with a progress bar and a try/finally that clears it. Results go to a log file, not only the Console.
- Editor-only code in an `Editor` folder; no `using UnityEditor` in runtime files (`project-structure-layout`). Namespace `Game.Editor`.
- Mutate prefabs through `PrefabUtility.LoadPrefabContents` / `SaveAsPrefabAsset` / `UnloadPrefabContents` in try/finally; scenes through the open scene and `MarkSceneDirty`, then save.
- Bounded automatic fixing: a tool that applies fixes counts attempts per target (max 2) and leaves the rest to a human.
- Never use `[InitializeOnLoadMethod]` to re-edit assets on every reload (one-shot migrations are run once and deleted). Never rename folders inside `Library/PackageCache` at build time. Never expose an unauthenticated command bridge (a local socket that runs menu items or writes scripts is local code execution): use the maintained MCP package.
- Language: English comments; UI via `EditorWindow` (Odin windows only behind `#if ODIN_INSPECTOR`).

## 2. The kit, ranked (details and ports in `references/tool-catalog.md`)
| # | Tool | Menu / entry | Owner skill |
|---|---|---|---|
| 1 | Scene optimizer orchestrator: one menu + hotkey calls every `IEditorBakeable` in the active scene (mesh combiner bake, distance-cull fetch, NavMesh, waypoints) | `Tools/Scene Optimizer/Bake` | `scene-optimizer-bake`, `mesh-scene-combiner`, `culling-group-distance` |
| 2 | Data and play helpers: clear save data / PlayerPrefs / caches, open data folder, pause (F2), slow-mo (F3), reload scene (F5), screenshot (F4), open build scene N (Shift+digit) | `Tools/Data/*`, `Tools/Game/*` | `data-persistence-facts` |
| 3 | QA ink loop: dump live UI rects + screenshot, `ink_audit.py`, bounded `Apply Ink Fixes` | `Tools/Qa/*` | `ui-ink-audit`, `ui-layout-audit` |
| 4 | Greybox to final pass: Prefab Replace, Collider Extractor, Material Collector, Material Match Finder, Find Missing Components | `Tools/Map/*` | `editor-bake-safety`, `one-material-world-shader` |
| 5 | Audio Config Generator (clips -> one config asset per clip, idempotent by path) | `Tools/Audio/*` | `game-audio-system`, `audio-import-and-mixer-optimization` |
| 6 | Localization glyph preloader / exporter (all keys x locales into the font atlas, then switch to static) | `Tools/Localize/*` | `localization-pipeline`, `tmp-font-optimization` |
| 7 | Mock toggles (ads native, IAP, subscription) with a menu check mark | `Tools/Game/Mocks/*` | `ads-layer-generic`, `iap-catalog` |
| 8 | Vendor SDK extension by partial classes in a project-owned folder (never edit the SDK) | n/a | `monetization-integration` |
| 9 | MCP wiring: package + per-project `.mcp.json`, `UserSettings` ignored, never commit tokens | n/a | `unity-mcp-workflow` |
| 10 | Optional: character component copy (two-pass joints), debug vertex colours, nav link creators, texture auto compressor, batch GPU-instancing | `Tools/*` | `nav-traversal-link-tool`, `import-presets` |
Samples: `references/samples/Scene_Optimizer.cs.txt`, `Data_Menu.cs.txt`, `Bounded_Fix_Attempts.cs.txt`. Check the installed SketchEngine package for editor menus before re-creating any (`rg "MenuItem" Packages/com.sketchengine`); re-create only what is missing (clear data, hotkeys, find-missing, texture compressor).

## 3. What the reference project lacks: add these (samples in `references/samples/`)
1. Tests: `Tests/EditMode` and `Tests/PlayMode` asmdefs plus static-check tests (no missing scripts, factory <-> asset 1:1, file == class, no tracked generated folders, ids unique). Policy in `project-structure-layout`.
2. Build/version method: a static `-executeMethod` entry that sets version and build number from args/env, builds AAB/APK, exits non-zero on failure. Reuse `unity-batch-build` (`BuildCli`); version has one source. Sample: `samples/Build_Version.cs.txt`.
3. Pre-commit check: a hook that runs a batch "missing script / missing reference" check on staged scenes and prefabs, and rejects ignored-folder losses. Samples: `samples/pre-commit.sh`, `samples/Check_MissingReferences.cs.txt`. Install with `git config core.hooksPath tools/githooks`.
4. CI: a pipeline (GitHub Actions or a local runner) that compiles, runs EditMode tests and the missing-reference check on every push; builds only at tags. Sample: `samples/ci-workflow.yml`; needs a Unity license secret, so ask before wiring remote CI.
5. Commit-msg hook and release script: see `git-hygiene-conventions`.

## 4. Done check
Each installed tool listed in the project's onboarding doc with menu path and owner skill; run twice with zero diff; the batch check returns exit code 0 on the project and 1 on a deliberately broken prefab; hooks installed on a fresh clone with one command.

## Pitfalls
- Tools that need Odin break on a project without it: gate with `#if ODIN_INSPECTOR` or use `EditorWindow`.
- Bake results live in scene data: save the scene after the bake (the tool only marks it dirty).
- `Assets/Create` or capture hotkeys that write screenshots into `Assets/` pollute the repo: write outside `Assets/` or ignore the folder.
- Move/Copy asset tools change paths: commit first.
- Name collisions silently overwrite (clip names in two folders): detect and report instead.
