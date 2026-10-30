---
name: ui-currency-bar-contract
description: Contract for every currency bar (cash, gems, speed, jump count...) in HUDs, shop headers and popups: one shared bar prefab where the icon OVERHANGS the left edge of the frame, number in the free gap, optional plus button; never an icon squeezed inside the frame. Use when building, copying or fixing any currency bar, shop header bar or balance pill.
triggers: currency bar, balance bar, cash bar, gem bar, money bar, shop header, thanh tien, thanh gem, thanh cash, icon trong frame, header shop
---

# Currency bar contract (any game)

Every currency bar anywhere (gameplay HUD, shop header, popup header, minigame HUD) is the SAME component:
1. One shared prefab (e.g. `UI_CurrencyBar`) per project, instantiated everywhere. Never rebuild a bar by hand in a shop/popup builder and never copy-edit it: variants differ only by icon sprite, value binding and an optional plus button.
2. Anatomy (fixed): dark rounded FRAME pill; ICON sits at the LEFT EDGE and OVERHANGS outside the frame (icon centre on the frame's left edge area, icon height about 1.0-1.4x the frame height, vertically centred); the NUMBER sits in the free gap between the icon's right edge and the plus button (or the frame's right inner edge), outlined, autosize with a sane min, centred in that gap; optional PLUS button at the right end inside/overlapping the right edge as in the reference bar.
3. Forbidden: the icon placed INSIDE the frame (icon + number crammed into the pill), a different font size per place, a different frame sprite per place, a hand-made header bar in a shop.
4. Sizes: icon and number size follow the reference bar; a bar in a tight spot is scaled uniformly (never re-laid out); stacked bars keep >= icon-overhang + 8 px between rows so overhanging icons never overlap the next bar.
5. Reuse check (mandatory when you touch UI): `grep` the project for a second implementation of a currency bar (names like CurrencyBar, MoneyBar, GemBar, Header currency, KT/Knife variants). More than one = merge them into the shared prefab; the shop headers must be instances of it.
6. Audit: add/keep an audit rule that flags a currency bar whose icon rect lies fully inside its frame rect (icon centre x > frame left edge + icon width/2) or whose prefab is not an instance of the shared bar; the batch UI audit must report 0 before any UI task is done.
7. Verify: screenshot the bar in every place it appears (each HUD, each shop header, each popup) and compare to the reference bar; print icon rect vs frame rect.
