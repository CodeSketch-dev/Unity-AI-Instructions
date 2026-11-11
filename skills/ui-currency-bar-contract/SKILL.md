---
name: ui-currency-bar-contract
description: "Contract for every currency bar (cash, gems, counters): one shared prefab, icon OVERHANGS the left frame edge, number in the free gap, optional plus. Use when building, copying or fixing a currency bar, shop header or balance pill."
triggers: currency bar, balance bar, cash bar, gem bar, money bar, shop header, thanh tien, thanh gem, thanh cash, icon trong frame, header shop
---

# Currency bar contract (any game)

Every currency bar anywhere (gameplay HUD, shop header, popup header, minigame HUD) is the SAME component:
1. One shared prefab (e.g. `UI_CurrencyBar`) per project, instantiated everywhere. Never rebuild a bar by hand in a shop/popup builder and never copy-edit it: variants differ only by icon sprite, value binding and an optional plus button.
2. Anatomy (fixed): dark rounded FRAME pill; ICON sits at the LEFT EDGE and OVERHANGS outside the frame, BIGGER than the frame (about 1.3x its height) and shifted slightly inward so it fully COVERS the rounded left cap: no frame edge may peek out beside or around the icon (owner: "no gap"); the NUMBER sits in the free gap between the icon's right edge and the plus button (or the frame's right inner edge), outlined, autosize with a sane min, centred in that gap; optional PLUS button at the right end inside/overlapping the right edge as in the reference bar.
3. Forbidden: the icon placed INSIDE the frame (icon + number crammed into the pill), a different font size per place, a different frame sprite per place, a hand-made header bar in a shop.
4. Sizes: icon and number size follow the reference bar; a bar in a tight spot is scaled uniformly (never re-laid out); stacked bars keep >= icon-overhang + 8 px between rows so overhanging icons never overlap the next bar.
5. Reuse check (mandatory when you touch UI): `grep` the project for a second implementation of a currency bar (names like CurrencyBar, MoneyBar, GemBar, Header currency, KT/Knife variants). More than one = merge them into the shared prefab; the shop headers must be instances of it.
6. Audit: add/keep an audit rule that flags a currency bar whose icon rect lies fully inside its frame rect (icon centre x > frame left edge + icon width/2) or whose prefab is not an instance of the shared bar; the batch UI audit must report 0 before any UI task is done.
7. Verify: screenshot the bar in every place it appears (each HUD, each shop header, each popup) and compare to the reference bar; print icon rect vs frame rect.

- Side-by-side bars (shop/popup header): switching to overhanging icons needs the row gap raised to >= overhang (~0.57 x frame height) + 8, else the right bar icon covers the left bar end. Bakes run while the Editor still compiles use the OLD constants: read a constant back (e.g. return it from the bake script) before trusting a bake.

- Same plate everywhere: shop/popup headers must NOT use a lighter/alternate plate option; a guard test walks every baked UI prefab and fails on any currency bar whose plate sprite differs from the HUD one or whose icon sits inside the frame.

## One value size across bars (measured trap)
- Autofit with a large fontSizeMax makes a 1-digit value render huge (55) while "240.8K" shrinks to 32 in the same HUD column: the gem bar looked oversized next to cash. Put ONE shared max (about the size the longest realistic value settles at, e.g. 36) in the shared bar builder; autofit may only shrink from it. Never pass a per-bar max.
- Audit: dump fontSize/fontSizeMax of every bar value in Play (CoinPill/GemPill/BagPill and shop-header copies); sizes of short values must not exceed the cap. Re-bake all UI prefabs after changing the builder (chunk the bake menus, 2-3 per MCP call) and rebuild the UI factory.
