# Pattern: skin-shop (list + preview)

Mockups (`mockups/`): `a-purple-frame-full.png` = full popup with header; `b-*.png` = body in another theme (equipped, IAP price, free-via-ad, equipped green card). Same structure in both games.

## Regions (landscape popup; structure per `unity-ui`: Root > Window)
```
[ Header: title (center), close X (top-right) ]
[ Board (left ~60%)                ][ Preview panel (right ~40%) ]
[  scroll grid, 3 cols, slim bar   ][  name (opt, top)          ]
[  at right edge of the board      ][  preview (2D or 3D)       ]
[                                  ][  stat line (opt)          ]
[                                  ][  ACTION BUTTON            ]
```
- Board: inset ScrollRect smaller than its frame, rounded mask, slim separate vertical scrollbar, next row partly visible as scroll hint (`ui-scroll-board`).
- Cell: square card, head/icon image, optional name label at bottom, badge slot top-right.
- Preview panel: own background, preview fills most of the height, action button at the bottom, equal margins.

## Cell states (priority order)
| State | Visual |
|---|---|
| locked | darkened card/icon + lock badge (corner or centered) |
| unlocked | normal card |
| selected | yellow outline (independent of ownership) |
| equipped | green check on card (A) or green card fill (B) |
Selection and equipped are separate: tapping a cell only selects and updates the preview.

## Action button (one button; state from the SELECTED item)
| Condition | Label / look | Tap |
|---|---|---|
| owned and equipped | "Equipped", gray, non-interactive | none |
| owned, not equipped | "Equip", green (inferred, not in mockups) | equip, move marker, sound |
| locked, paid IAP | price text (e.g. 4.99$), green | start IAP (`unity-iap-port`) |
| locked, ad unlock | ad icon + "FREE", green | rewarded ad (`monetization-integration`); on success unlock + equip |
| locked, soft currency (variant) | price + currency icon; unaffordable = red text | spend via wallet |
| locked, other: level/zone/rebirth (variant) | requirement text, gray | requirement toast |
Persist unlocks through the project data block; never grant before the purchase/ad callback.

## Preview
Interface `ISkinPreview { Show(id); Clear(); }`, two interchangeable implementations chosen by variant:
- **2D (default for low-end / many items)**: one baked transparent PNG per item (editor bake from the 3D prefab) in an Image/RawImage. Zero runtime cost.
- **3D (premium look; use when the character is already a 3D prefab)**: one preview stage prefab outside the play area (own layer, own light), one dedicated camera rendering to a RenderTexture (~512x512, no MSAA, no shadows) shown in a RawImage. Swap skins by running the real skin-apply code on the stage model. Idle animation + optional drag-to-rotate. Enable camera/stage only while the popup is open; one preview rig for the whole game; release the RT on close. Transparent background: clear to alpha 0 with an alpha-capable RT format.
Both: update on selection only, never per frame; locked items may show a dark silhouette (variant).

## Binding (per game)
- Item record (config/factory): id, display name, icon/preview source, unlock type (free / IAP id / ad / currency price / requirement), optional stat (label + icon + value).
- Data block: unlocked ids, equipped id (framework data/save pattern).
- Events (StaticBus when installed): `Skin_Equipped(id)`, `Skin_Unlocked(id)`; gameplay and HUD react to events, no popup-to-gameplay calls.
- One `SkinApplier` entry point used by both gameplay and the preview stage.

## Variants (resolve before building; default first)
1. Name on card: hidden / shown (A).
2. Equipped marker: green check (A) / green card (B).
3. Lock: corner badge (B) / centered (A).
4. Preview: 2D baked / 3D RenderTexture.
5. Name + stat line in preview panel: off / on (A).
6. Unlock types used by this game: free, IAP, ad, currency, requirement.
7. Category tabs above the grid: none / tabs.

## Fixed vs flexible
Fixed: cell states and priority, one action button driven by the selected item, `ISkinPreview`, binding records, events, persistence. Flexible: positions, sizes, column count (3 default), panel ratio, button placement, header content, extra buttons.

## Checks
Every state and every button condition screenshotted; scroll reaches the last item without overflowing the frame; selecting never changes ownership; restart keeps the equipped item; 3D preview camera off when the popup is closed; Console clean.
