---
name: shop-tab-page-checklist
description: Use when building or fixing any in-game shop with a tab column and card pages (gem/cash/offers/treadmill/trail): tab spacing, tab label size and gap-centring, card ordering by price, sparkle fx only on the best card, header currency text. Lessons from fixing a shop three times.
triggers: shop, tab, offers, tab text, card order, sparkle, pack, gem pack, shop tab, cua hang, sap xep, goi
---

# Shop tab + card page checklist

Check these BEFORE reporting a shop done; verify in Play with a real screenshot, never ask the user to look.

1. **Tab spacing**: search runtime code that re-spaces the tab list (e.g. a "fill the height of N tabs" formula). A hidden tab changes N and spreads the visible tabs far apart. Keep the authored spacing (about 8 px for 100 px tabs).
2. **Tab size and label**: tabs about 100 px tall (not ~80); label font as large as the longest label ("TREADMILL") allows in the free gap right of the icon art. Measure the icon's visible right edge from the sprite alpha (not its rect), gap = [iconVisibleRight + 6, tabWidth - 12], text rect symmetric about that gap, same font size on every tab. Widest tab is bounded by the clipped tab column viewport: check the pill is not cut.
3. **Card order**: pinned special offer first (e.g. x2 boost), then by Gem price descending; sort at runtime by the product price, not by prefab order. Tabs with a clone loop: reorder after all clones exist.
4. **Sparkle fx** (ray + shine + sparkles + hero float): only the pinned card and the best (most expensive) card keep it; strip Shop_PackFx and FxClip from the others at open. Rank-1 fx must not scale the card: only icon float/breathe and the buy button animate.
5. **Value text under the icon** ("+30T"): centre it vertically in the free band between the icon bottom and the buy button top (or the bonus row when shown), as large as the band allows (font about 0.8 x band height).
6. **Header currency**: number centred in the gap between icon right edge and plus left edge with >= 6 px padding; it must autosize, never touch the plus.
7. **Prefab saving trap**: components that animate in the prefab stage (pack fx) overwrite edits and bake animated scale/position on save. Disable them, edit, re-enable, SaveAsPrefabAsset in the same call, then re-open and read the values back. Never use world corners of a prefab loaded outside a canvas for layout maths: use serialized sizes/offsets.
