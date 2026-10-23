---
name: ui-clone
description: UI hub for recreating a reference UI (HUD, popups, shops, boards) and routing to the other UI skills. Use when UI must look/behave like another game or shows wrong 9-slice/anchors/overlap/mirrored text.
---

# UI clone (UI hub)

Route UI work to one skill per concern; load only what the task needs:
| Concern | Skill |
|---|---|
| Standard screens (skin shop, shop, popups): fixed structure, game supplies art | `ui-pattern-library` (check first) |
| Canvas/SafeArea/PopupRoot structure, validation at 3 aspect ratios | `unity-ui` |
| Where each HUD element goes, sizes, thumb reach | `mobile-hud-layout` |
| Matching a reference screen or demo image 1:1, build/compare loop | this skill + `ui-popup-from-demo` |
| Standing visual rules (icons, ad badge, text, dim, NEW tag) | `ui-style-rules` |
| Scroll lists, shop grids, preview panels | `ui-scroll-board` |
| Rewards flying into HUD currency | `currency-spread-fx` |
Precedence when they disagree: reference/spec > user's latest message > `ui-style-rules` > `mobile-hud-layout` defaults.


## Method
1. **Inventory the reference screen** from screenshots/prefabs: every element, its sprite, anchor, size, color, font and behavior (tap, fade, slide, pulse). Number them.
2. **Reuse before recreate**: transfer the original sprites/atlases (see `asset-transfer-closure`), then use the project's existing UI framework (popup manager, button kit). Don't build a parallel UI system.
3. **Layout**: anchor to screen edges/corners like the reference, using the zone map and sizes in `mobile-hud-layout` as the baseline (the reference wins when it differs); test several aspect ratios (tall phone, 16:9, tablet) in the Game view; respect the safe area.
4. **9-slice**: set sprite borders in the importer, set Image type to Sliced, check the minimum size. Broken frames are almost always missing borders or a Simple image type.
5. **No-overlap rule**: list all HUD buttons with their rects and confirm no pair overlaps (jump, attack, contextual pick-up/drop, hotbar, currency, menu). Contextual buttons that swap (Attack <-> Drop) share one slot.
6. **Text**: pick the project's text solution once. For performance, batch world-space text into one system, keep rich-text colors working, and only reassign text when the value changes.
7. **World-space UI** (boards, labels): decide billboard vs fixed from the reference. Give interactive ones a real collider/raycast target, range-based fade that also disables raycasts, and verify text isn't mirrored (scale sign and facing).
8. **Perf hygiene**: separate static and dynamic canvases, disable Raycast Target on decorative graphics, disable layout groups once they have laid out.
9. **Compare** with the reference screenshot at the same resolution, list deltas, then run `done-means-wired`.

## Lessons from real runs
- **Port, don't approximate**: if the reference has the UI prefab/atlas/sub-sprite, port it and keep position, size, hierarchy, frame and icon identical (see `reference-port`). Only create a new texture after confirming the reference lacks it.
- **Fix systemic problems systemically.** A text baseline that sits too low on every label is a bug in the shared text creation/setup, not in each label; fix the shared setup once, then re-check header, buttons, popups and world labels. Same for button press-scale (apply through the shared press component, including world-space buttons).
- **Sliced art stays sliced**: biome ribbons, frames and pills that carry sprite borders must use `Image.Type.Sliced` in the generated prefab *and* in the UI builder; stretched Simple images produce long distorted bands.
- **Builders own their output**: if an editor builder regenerates a HUD hierarchy, change the builder and re-run it. Hand edits to the output (including deleting an old button) are lost or collide on the next build.
- **Contextual buttons**: one slot with icon/label swap (Pick up <-> Drop) instead of separate buttons; keep >= ~44 px gaps and clear distance from the hotbar.
- **Info cards** (carried item, region label) must not sit under the hotbar; region labels can shrink after the intro.
- **Price/affordability colors**: unaffordable price text turns red; verify live, not only in the prefab.
- **World boards** (upgrade boards) need a real tap collider, range-based fade that also blocks raycasts, and must be tappable from the distance the reference allows.
- Remove improvised placeholder icons (e.g. a black "!") and use the reference warning asset or hide the element.

## Lists, boards and previews
Shop/inventory popups with a scroll list and a preview follow `ui-scroll-board` (inset ScrollRect with rounded Mask, spaced cells, slim separate scrollbar, dark preview stage, colour per item state; reward = pink-purple with ads icon and "FREE").

## Notes
Animated entrances (banner slide + fade, popup scale-in) are part of fidelity. Take timing and easing from the reference instead of inventing them.

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.
