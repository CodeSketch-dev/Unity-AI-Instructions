---
name: unity-ui
description: "Canvas/popup structure for mobile uGUI: root canvas, SafeArea, PopupRoot, anchors, banner clearance, layout validation. Use when creating or changing any Canvas, HUD, popup or panel prefab."
---

# Unity UI

Mobile landscape (Android/iOS, incl. low-end). Values: project `project-config.yaml` (template in `templates/`) > defaults here.

## Structure
- One global root Canvas: Overlay, Sort Order very high so nothing renders above it (default 30000; any value in that range is fine, e.g. an existing 25060 stays, don't change it), Scale With Screen Size, Match Mode **Expand**, ref. res. `ui.referenceResolution` (default 1920x1080; some games 1280x720). No extra root canvases; nested Canvas only for measured rebuild isolation.
- Hierarchy: `GameSingleton > Canvas > Root > {SafeArea, ViewContainer, PopupRoot, LoadingScreen?}`. Sibling order = z-order, bottom to top. Don't reorder or add layers without approval.
- Every Canvas/view/popup prefab: exactly one empty child `Root` (stretch full, zero offsets, no Graphic); all content under it.
- Persistent HUD lives under `SafeArea` (stretch RectTransform + `UISafeArea`, Conform X/Y on). Full-screen backgrounds/dim layers: stretch.
- `ViewContainer` object carries the `ViewContainer` component; `PopupRoot` object carries `PopupRootSetter` (registers itself as `PopupManager` root). Add these to the objects; don't invent other scripts.
- Popups = anything a button opens. Own prefab, stretch-full root, `Popup` script if present, spawned with `PopupManager.Create(prefab)` (SketchEngine; adds it under `PopupRoot`). Never `Instantiate` into a Canvas, never nest in a view.

What the reference projects do (canvas table, sort orders, safe area, joystick): `references/canvas-reference.md`.

## Reuse (framework-first)
Before writing any UI helper/prefab (`UISafeArea`, `FloatingJoystick`, `PopupManager`, `Popup`, buttons, bars, sprites, fonts, TMP styles) search the open project only (its `Assets/`, `Packages/` and `Library/PackageCache/`, since git packages such as `com.sketchengine` live in the cache; never parent folders or sibling projects) and use it. Match existing art style. If none exists (other teams' projects): create the smallest project-side equivalent with the same name, say so in the report. Never edit framework/package code. Existing prefabs may predate these rules (AI-generated projects): reuse their parts (sprites, headers, buttons, styles) but this skill's structure rules win over copying their layout, and never switch their text component (e.g. UniText vs TMP) on your own.

## Layout rules
- Never assume 16:9 (Expand adds width on 20:9, height on tablets): anchor to the owning edge/corner, no center-based absolute coordinates.
- No element touches or sits near a screen edge. Choose a consistent, size-proportionate margin yourself; layout must look balanced (even spacing, aligned, symmetric left/right).
- No UI element overlaps another, including conditional ones (e.g. Pick up). Use explicit rects or Layout Groups.
- Bottom clearance: all gameplay UI stays >= `ui.banner.reservedHeight` (default 200) above the bottom, banner shown or not. Bottom anchors measure from above it.
- Popup/panel: buttons never near the panel edge (comfortable inner padding). Center of gameplay view stays free.
- Non-interactive Graphics: Raycast Target off.

## HUD zones
Zone map, sizes and thumb rules: `mobile-hud-layout` (single source; do not duplicate it here). Project-specific additions: joystick object `Move` = transparent touch region (Image no sprite, Raycast on), default anchors (0,0)-(0.35,0.6) (`ui.joystick.touchRegion`), max left half, keep prefab fields; toolbar/hotbar bottom-center above bottom clearance between joystick and interact group; empty zones stay empty.

## Procedure
1. Read project-config and existing UI prefabs; don't rescan unchanged files.
2. Edit the source prefab, not a scene override.
3. Anchors/pivots first, then offsets.
4. Validate: screenshot Game view at ref. res., 2400x1080 (20:9), 1600x1200 (4:3); check edges, overlap, bottom clearance, safe area; fix cramped/misaligned items; no missing refs; Console clean.

## Output
Changed prefabs/scenes, config values used, rules not verified, helpers created.
