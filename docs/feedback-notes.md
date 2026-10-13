# Feedback notes

## Skills repo (2026-10-14)
- Skills are written in English, short, token-lean; chat stays Vietnamese. Why: lower token cost.
- Layout rules are qualitative (no invented numbers). Only user-stated numbers are kept (bottom clearance 200, canvas sort order ~30000, joystick touch region 0.35x0.6, max left half).
- `unity-ui` rules are the standard even when existing prefabs differ (e.g. popups without a `Root` child). Existing prefabs are reused for parts/styles, not for structure.
- `break-and-steal-unity` is vibe-coded (not a reference). `knife-tower` is hand-coded (reference for conventions).
- Framework pieces (`UISafeArea`, `PopupManager`, `PopupRootSetter`, `Popup`, `ViewContainer`) come from SketchEngine, installed as a git URL package (`com.sketchengine`, lives in `Library/PackageCache`). Skills must say "search first, create only if missing" so other teams' projects don't break.
- Claude tends to regenerate helpers that already exist (e.g. safe area): always search the open project first, never sibling projects.
- Skills are developed only in this repo (Unity-AI-Instructions). Open Unity projects are reference/test only; do not change them to build skills, and ask before writing test artifacts there.
- Goal: new projects built ~3x faster (3 days -> 1 day) with correct output first try. Be flexible: follow the intent, not exact numbers. Root canvas Sort Order only needs to be "very high" (30000 default; existing 25060 is fine, don't change it). Why: values came from earlier vibe setups.
- Toolbar/hotbar (multi-slot bar, contents per game) defaults to bottom-center, above the 200 bottom clearance, no overlap with joystick/interact group.
