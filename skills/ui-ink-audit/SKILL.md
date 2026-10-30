---
name: ui-ink-audit
description: Use automatically after ANY UI change or screenshot: pixel-measure every button/pill/frame with icon + text (centre on the MEDIUM face band, no outline/light/shadow) and every popup title (centre on colour band), then auto-fix with HorizontalLayoutGroup padding until <= 2 px.
triggers: align, canh giua, lech, button, icon text, hatch, price, pill, title, header, popup, shadow, outline, ink, screenshot, ui audit
---

# UI ink audit (automatic, no reminder needed)

Rects lie. Buttons are sprites with bands top to bottom: dark OUTLINE, LIGHT highlight, MEDIUM face, SHADOW lip, OUTLINE. The icon + label pair must be centred on the MEDIUM face only (light, shadow and outline excluded), horizontally and vertically. A title is centred on the colour band of the header (`ui-title-band-centering`).

## Rule 0 (construction)
Every button / pill / frame holding icon + text is ONE `HorizontalLayoutGroup` (icon first, label second, MiddleCenter, Capline text, spacing 5/10/15). Its top/bottom padding carries the light/shadow asymmetry. Never a hand-positioned icon beside a stretched label.

## Procedure (run it yourself after every UI edit, every screenshot showing UI, every new popup/minigame/project)
1. Play Mode, claim blocking popups, open the screen.
2. `Qa_InkDump.Run(path)` (copy `Qa_InkDump.cs.txt` from this folder into `Assets/<game>/Scripts/Editor/Qa/Qa_InkDump.cs` if the project lacks it) writes json: per Selectable the screen rect, icon rects, text-ink rects, `hlg` flag, canvas scale; per `*Title*` label its ink rect and a probe column. `ScreenCapture.CaptureScreenshot` in the same frame; read the png next call.
3. `python ink_audit.py shot.png dump.json` (this folder). For each button it finds the MEDIUM face (most common colour of the centre area; extent along the inner left column and a row below the top, so outline, light and shadow rows are excluded), measures white text ink + icon union, and reports dx/dy to the face centre, ink leaving the face, overlap with other buttons, missing HLG; for titles dy to the band centre.
4. Every FAIL prints the fix (HLG padding units = px*2/scale). Apply it on the SOURCE prefab (animated components disabled while saving), re-run until `0 fail` (tolerance 2 px). Frames and cards: same procedure with the frame as the item.
5. Report the printed ok/fail numbers and look at the screenshot once. Never ask the user to screenshot and re-request.

## Gotchas
- Dominant-colour face detection fails on gradient/texture buttons: say so and verify by eye on a zoomed crop.
- Text ink = near-white pixels; coloured text needs its colour added to `ink_bbox`.
- `ScreenCapture` includes overlay UI only; camera canvases need a game-view capture.
