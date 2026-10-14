---
name: ui-pattern-library
description: Reusable game-independent UI patterns (skin shop, shop, popups) with layout contract, states, behavior and variants; only art/theme and content change per game. Use before building any shop/skin/list+preview/popup screen, or when told "same format as our other games".
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
4. Build with the project's popup/UI framework and an idempotent builder (`ui-popup-from-demo`, `editor-tool-authoring`); lists via `ui-scroll-board`; rewards via `currency-spread-fx`; rules via `ui-style-rules`.
5. Compare with the mockup, verify at 3 aspect ratios (`unity-ui`), then `done-means-wired`.

## Flexibility contract
- **Fixed**: states, action-button logic, binding interfaces, event flow, script naming. This keeps code consistent across games.
- **Flexible**: positions, sizes, columns, panel ratio, button placement, tabs, extra elements. Follow the dev's request over the mockup; keep every fixed item.
- A deviation worth reusing -> note it in `docs/feedback-notes.md`; if it applies to all games, update the pattern.

## Adding a pattern
Folder `patterns/<name>/` with `pattern.md` (model: `skin-shop`, <= ~80 lines) + `mockups/`; add one line to `patterns/index.md`.
