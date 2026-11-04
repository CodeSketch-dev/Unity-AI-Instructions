---
name: kit-ui-services
description: "Use when building or importing reusable UI service prefabs from the studio kit: popup shell and facade, currency bar and fly-in, tabbed shop, IAP card, daily login, revive, settings, rating, quest arrow/focus, toast. Opt-in kit; pick the parts you need."
triggers: ui kit, popup facade, popup shell, currency bar, currency spread, shop tabs, iap card, daily login, revive popup, settings popup, rating popup, quest arrow, focus pointer, toast, floating text, kit ui, knife tower style ui, bo ui co san, popup mau, thanh tien, cua hang tab
---

# Kit: UI and services

Opt-in kit (see `prefab-kit-catalog`). Everything here is a pattern to re-author with the new game's art, not files to copy blindly. Check the installed SketchEngine package API first (`Popup`, `PopupManager`, `StaticBus`, `PoolPrefabGlobal`, `UINotificationText` live there); check referrers before importing any reference prefab.

## 1. Rules that hold for the whole kit
1. Popup = prefab (stretch root + CanvasGroup + `Popup` + data-driven animation list: Background alpha 0.7-0.94, Scale 0.3 -> 1 ease out-back). Opened only through a static Factory facade (`Factory_X.Show...`) that holds the prefab ref in a `ScriptableObjectSingleton`; a singleton guard stops double-open. Never `Resources.Load` or scene-placed popups.
2. Pages never reference tabs: one event (`Event_Shop_TabSelected`) selects the page, so "open shop at tab X" works from anywhere (e.g. "not enough gems").
3. One currency bar prefab reused in HUD, shop and popups. Data changes first, then an event starts the fly-in; the bar snaps to `value - amount` and counts up when the first item lands (`reachEndDelay`). Never set the label by hand. Skill: `ui-currency-bar-contract`, `currency-spread-fx`.
4. Grant rewards after the popup closes (`Popup.OnCloseEnd`), so the player sees the fly from the popup icon to the bar.
5. Display values come from data (IAP catalog, daily asset, config), prefab text is placeholder only. Product ids, placement ids and message strings are replaced per game and localized.
6. Prefer one prefab + data over variants (premium/special copies were deleted upstream); nest one prefab per shop tab, not one 900-line prefab.
7. Decide the overlay stacking contract first (tutorial focus above popups, below the loading fade, above banner/native zones): `native-ad-beside-popup`.
8. Popups are instantiated on open, which is fine for rare screens; per-hit UI uses pooled `Text_Spread` + `PoolPrefabGlobal`.

## 2. Parts (ranked, universal first)
| Part | Genre | Notes | Detail |
|---|---|---|---|
| Popup shell + facade | all | stable contract above | references/recipes.md A |
| Currency bar + spread | all with a soft currency | juiciest feedback in the kit | B |
| Quest focus pointer (hand), focus message, ground arrow | all with a first-time flow | skill `tutorial-focus-notice-hand`, `tutorial-phase-system` | C |
| Toast + pooled floating text | all | one-slot toast so messages never stack | D |
| Tabbed shop + IAP card | monetised | `shop-tab-page-checklist`, `iap-catalog`; add a parental gate before purchases | E |
| Revive / continue offer | runner, obby, survivor | timeout, X and decline are ONE path | F |
| Settings, daily login, rating | mobile live-ops | `settings-pause-offline`, `rating-prompt-flow` | G |
| Cheat menu | all (dev builds only) | strip in release | H |
| Jackpot slot, gacha box | optional casual pack | always show odds and a pity counter | I |
| Nav traversal link | bots on NavMesh | `nav-traversal-link-tool` | J |

## 3. Import checklist
- Grep the reference for referrers of each prefab GUID (dead prefabs exist: unused bars, old buttons, duplicated packs).
- Bring the dependency closure (`asset-transfer-closure`): script + .meta GUID, sprites, materials, shader graph, fonts, config SO.
- Layout contract of the host project applies after import: `ui-always`, `ui-layout-audit`, text outline, 12 px spacing, safe area.
- Wire in the scene: popup canvas root setter, persistent overlay container for tutorial prefabs, bar prefab nested in HUD and shop.

## Done-check
Popup opens from a facade call with no scene reference; reward fly-in lands on the shared bar and the number counts up on arrival; "buy" with missing currency jumps to the right shop tab; Play screenshot per popup; audit totals 0 violations; no hard-coded product id or string left.

## Pitfalls
- Tutorial `onReached` callbacks repeat every frame inside the threshold: latch them or stop on reach.
- Arrow texture Wrap Mode must be Repeat; Hand and arrow art must stay tracked in git (an ignore rule once dropped the hand sprite).
- Ads cover UI: tutorial text hidden under the banner was fixed 3 times upstream.
- Fonts/materials drift across 3 families: pick one font + one outline preset family on day one; localize every label from the start.
- Several sprite versions with the same name: keep one atlas per UI theme.

References: [recipes](references/recipes.md), [images](references/images/README.md), [PROVENANCE](references/PROVENANCE.md).
