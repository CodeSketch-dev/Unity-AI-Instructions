---
name: unity-project-bootstrap
description: "Set up a new Unity 6 mobile project: packages, folders, asmdefs, URP tiers, platform settings, scene flow, git ignore/LFS, first compile check. Use when starting a game or \"init the project\"."
---

# Unity project bootstrap

Do the boring foundations once and correctly: everything later (perf, builds, MCP work) depends on them. Inspect what already exists before changing anything and never overwrite existing project settings without saying so.

## Steps
1. **Detect** Unity version, render pipeline, installed packages (`Packages/manifest.json`), existing folders and asmdefs. Read the global house-style instructions for folder names (`Assets/_Game`, `Assets/_Art`) and framework choices.
2. **Packages** (only what is needed and not already present): render pipeline (URP), Input System if the project uses it, TextMeshPro/UniText per team choice, UniTask, a tween library (one), Addressables if content is large, Unity MCP bridge for the agents. Ask before major version changes.
3. **Folders**: create only folders with real content; follow the house layout (`_Game/{Audios,Configs,Fonts,Materials,Prefabs,Resources,Scenes,Scripts/{Core,Data,Editor,Event,Factory,Logic}}`).
4. **Assembly definitions**: one for runtime game code, one for editor tools, optional for framework glue; avoids full-recompile pain and enforces layering.
5. **Rendering for low-end mobile**: Mobile URP asset + a PC/Editor asset with Quality levels mapped per platform; SRP Batcher on, one shadow cascade, 512-1024 shadow map, short shadow distance, no soft shadows, MSAA off/2x, HDR off, depth/opaque textures off unless required; linear vs gamma by art needs.
6. **Player settings**
   - Android: IL2CPP, ARM64 (+ARMv7 only if the audience demands), minimum API per current engine/Play requirement, target API per current Play policy (verify the latest), AAB, managed stripping Medium, texture compression ASTC, orientation locked per design.
   - iOS: IL2CPP, minimum iOS per engine support, camera/microphone usage strings only if used, orientation locked, ATT usage description only if ads need it.
   - Both: target frame rate 60 (or 30 for heavy scenes), `Screen.sleepTimeout = NeverSleep` during play, vsync off with explicit target, auto-graphics API choices verified.
7. **Scene flow**: `Boot` (init services, data load) -> `Loading` -> `Game`; additive scenes for UI/world when the team uses them. Editor-only conveniences (e.g. `Application.runInBackground = true` under `#if UNITY_EDITOR`) so MCP-driven testing continues when unfocused.
8. **Git**: Unity `.gitignore`, `.gitattributes` with LFS for large binaries (fbx, psd, wav, mp4), meta files visible, keystores and keys excluded.
9. **Logging and debug**: a thin logging wrapper, a debug overlay (FPS, memory) for devices, cheat menu behind a define for fast testing.
10. **Verify**: refresh/compile, zero Console errors, open `Boot` and press Play, build a development APK/IPA only when the user asks.

## Automation
For a new game use `new-game-bootstrap` (scripted token replace, settings applier, repo preflight) instead of repeating these steps by hand.

## Output
`docs/project-setup.md`: decisions taken (packages, tiers, settings) so the next agent does not re-derive them.
