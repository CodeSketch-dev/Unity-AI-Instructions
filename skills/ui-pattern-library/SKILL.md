---
name: ui-pattern-library
description: "Game-independent UI patterns (shop, settings, daily login, gacha, jackpot, rating, revive, inventory, rebirth, wheel, quests) with layout contract, states and variants. Use before building any shop, list, popup or page. Part of the ui-always set."
---

# UI pattern library

A pattern fixes structure and behavior; the game supplies art (theme) and content (binding). Result: every game's shop/skin/popup behaves and is coded the same, only the look differs.

## Three layers (never mix them)
1. **Pattern** (`patterns/<name>/pattern.md`): regions, slots, states, behavior, variants, hooks.
2. **Theme** (per game, `docs/ui-theme.md`, from `theme/theme.template.md`): sprites, colors, fonts, frame/button/lock/check/ad icons. Art references only, no layout.
3. **Binding** (per game): item list/config, prices, currencies, preview source, IAP/ad ids.

## Workflow
1. Read `patterns/index.md` (one line per pattern). Pick the pattern; open only that `pattern.md`. Open `mockups/` only to compare visuals.
2. Check `docs/ui-theme.md`. Missing -> create it from the template by asking the dev for art, or by listing existing sprites (`reference-index`).
3. Resolve every **Variant** line (ask ONE batched question for unclear ones; otherwise take the marked default).
4. Take the pattern's `spec.yaml` (numbered layout contract, 1920x1080), adjust it to the game's capture, then `ui-builder` (lint -> convert -> idempotent builder; `ui-popup-from-demo` for demo images, `editor-tool-authoring`); lists via `ui-scroll-board`; rewards via `currency-spread-fx`; rules via `ui-style-rules`.
5. Compare with the mockup, verify at 3 aspect ratios (`unity-ui`), then `done-means-wired`.

## Flexibility contract
- **Fixed**: states, action-button logic, binding interfaces, event flow, script naming. This keeps code consistent across games.
- **Flexible**: positions, sizes, columns, panel ratio, button placement, tabs, extra elements. Follow the dev's request over the mockup; keep every fixed item.
- A deviation worth reusing -> note it in `docs/feedback-notes.md`; if it applies to all games, update the pattern.

## Pattern folder contents
`pattern.md` (regions, states, behavior and hooks, binding, variants, checks; <= 80 lines), `spec.yaml` (layout contract in the `ui-builder` format: numbered elements, anchors, positions, sizes, `container` and `state` flags; leaf elements must not overlap and stay on screen, checked by `ui_spec_tool.py lint`), `mockups/wireframe.png` (numbered placeholder rendered from the spec; replace or complement with real captures). `skin-shop` is the older format (real mockups, no spec). Sizes marked VERIFIED come from the reference projects (report 07); patterns marked INFERRED (`spin-wheel`, `quests`, the compressed `vip-pass` heights) are designs to be re-measured from the target game's capture.

Regenerate a wireframe: `py -I <skills>/ui-builder/scripts/ui_spec_tool.py rects spec.yaml --out rects.json` then `py -I <skills>/ui-pattern-library/scripts/wireframe.py rects.json mockups/wireframe.png`.

## Adding a pattern
Folder `patterns/<name>/` with `pattern.md` (model: `settings`), `spec.yaml`, `mockups/wireframe.png`; add one line to `patterns/index.md`. `tools/tests/test_pattern_library.py` enforces the structure (index entry, <= 80 lines, Checks section, clean lint, dense numbering).
