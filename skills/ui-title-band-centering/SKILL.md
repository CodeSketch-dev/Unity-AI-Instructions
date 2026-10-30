---
name: ui-title-band-centering
description: Use when a popup/board has a title or header band and its title, icon or button must be centred on the visible colour band, or when text/hatch/price buttons look off-centre, or HUD bars move under a native ad. Pixel-measured, no guessing.
triggers: title, header, band, popup title, align title, center title, canh giua title, tieu de, hatch now, button lech, native dich bar
---

# Title band centring (measure the pixels, not the rects)

Popups are often ONE board sprite (sliced): the header band and the body differ only by colour. The rect of a `Header` object is NOT the visible band (it can be 95 px tall while the band is 150 px). Never centre a title on a rect, never nudge by eye.

Key idea: the title band and the body have DIFFERENT colours, so the colour change in a screenshot gives the true band height. Run `band_scan.py <shot.png> <x>` (this folder) to get the band top, face bottom and face centre in one call, then centre the title ink on that centre.

## Procedure (always, automatic for any popup title / header content)
1. Open the popup in Play at 1920x1080 (claim blocking popups first), `ScreenCapture.CaptureScreenshot` to the scratchpad, read it next call.
2. Scan one pixel column that crosses only the board (not text/icons, e.g. between title and close button) from the top: band face = first saturated colour run after the dark outline; band bottom = the colour change to the cream/body (the darker lip belongs to the band edge, not the face). Python/PIL: print `getpixel((x,y))` every 6 px.
3. Band face centre `Cband` (top-origin y). Title ink centre = `TMP_Text.textBounds.center` -> world -> `1080 - y`. Not rect centre (Capline/descender shifts it).
4. Set `anchoredPosition.y += (target - current) / canvas.scaleFactor` (lossyScale of the label) on the SOURCE prefab, save, re-measure: |dy| <= 2 px, and horizontal centre = board centre (or free gap between icon and close button when the board is asymmetric).
5. Header icon (egg/pet), close button and side buttons are centred on the same `Cband`; overhanging icons are judged by the band, not by their own rect.
6. A reference popup that already looks right (e.g. Welcome Back) is the benchmark: compare band-top to title-top and band-bottom to title-bottom screenshots side by side.

## Icon + label buttons that sit inside a row (hatch / skip / price)
- Children of a sub-root (e.g. `TimeRoot`) are positioned in THAT parent's space; compute the target in row coordinates, convert: `local = target - parentCentre - parentHalfWidth` for a right-anchored child.
- After placing, print rects of neighbours in the SAME space: gap >= 10 px between timer pill and button, button right edge >= 14 px inside the row border, no overlap with the left icon. Build icon + text as one HorizontalLayoutGroup; measure the pair centre, not the label.

## HUD bars and native ads
- A currency bar is identified by ANY of its markers (`Currency_Bar`, `Currency_ShopLink`, bar prefab name), not only one component. A relocation helper that matches by name (`money`, `speed`) will move bars that lack the marker: always exclude by every marker and verify by Play numbers (anchoredPosition + scale before/after the native half shows must be identical).

## Report
List the measured numbers (band centre, text centre, dy) per popup and attach the screenshot you looked at. No numbers = not done.
