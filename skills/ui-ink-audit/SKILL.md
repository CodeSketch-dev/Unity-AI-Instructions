---
name: ui-ink-audit
description: "Use on any UI edit, Play test or screenshot in every Unity project: audit UI by pixels (icon+text centred on the button face, titles on their band, no overlaps) and fix the [InkAudit] FAIL lines it reports."
triggers: align, canh giua, lech, button, icon text, hatch, claim, price, pill, title, header, popup, hud, shop, shadow, outline, ink, screenshot, ui audit, play test, qa
---

# UI ink audit (whole game, automatic)

Rects lie. Buttons are sprites with bands top to bottom: dark OUTLINE, LIGHT highlight, MEDIUM face, SHADOW lip, OUTLINE. The icon + label pair is centred on the MEDIUM face only, horizontally and vertically (tolerance 2 px). A header title is centred on its colour band (`ui-title-band-centering`). A row of buttons is centred on its board.

## Rule 0 (construction)
Every button / pill / frame holding icon + text is ONE `HorizontalLayoutGroup` (icon first, label second, MiddleCenter, Capline text, spacing 5/10/15). Top/bottom padding carries the light/shadow asymmetry. Never a hand-positioned icon beside a stretched label. Badges ("x2", dots) overhang on purpose and are excluded from the pair.

## Manual only (the automatic watcher was removed)
An always-on watcher costs real CPU in Play Mode (measured: about +160% of one core on top of the game's ~350%), which made the user's PC lag, so there is NO background watcher. The audit runs only when the agent asks for it:
1. Open the screen in Play, then `AiQa.Qa_InkDump.Run(json)` + `ScreenCapture.CaptureScreenshot(png)` in the same call (call it through reflection by type name `AiQa.Qa_InkDump`), then `python ink_audit.py png json [--fixes fixes.json]`.
2. Apply with `AiQa.Qa_InkFix.Run()` in Edit Mode (menu Tools/Qa/Apply Ink Fixes): changes are clamped (8 units per step, 16 max padding, skip when > 20), only failing items are touched. Always look at the screenshot afterwards; if a result looks wrong (tiny text, squeezed button) revert that prefab.
3. For judgment calls: take the screenshot and LOOK at it (or give it to an agent) before accepting any auto change.

Install: `sync.bat` copies `Qa_InkDump` and `Qa_InkFix` (`templates/unity-editor/AiQa/*.cs.txt`, namespace `AiQa`) to `Assets/_AiQa/Editor/` of every Unity project with uGUI/TMP, and `ink_audit.py` to `<project>/.claude/skills/ui-ink-audit/`. Needs `python` + Pillow.

## What the agent must do (every task, every Play test, every autoplay)
1. After UI work and after Play tests, audit the screens you touched or opened (steps above). A screen nobody opened is NOT audited.
2. Every FAIL line carries the fix (HLG padding units = px*2/scale, or move title N units). Apply it on the SOURCE prefab (stop Play first, animated components off while saving), re-run, repeat until `0 fail` for every screen touched. Treat a FAIL seen in any test as a bug of this task, not a note for the user.
3. Manual run: `Qa_InkDump.Run(json)` + `ScreenCapture.CaptureScreenshot(png)` then `python ink_audit.py png json`.
4. Report the screens audited with their fail counts. If python/Pillow is missing, say so and fall back to `ui-title-band-centering` measurements.

## Limits (say them, do not hide them)
- Face = most common colour of the button centre: gradient/textured buttons need an eye check on a zoomed crop.
- Ink = near-white text + visible icon pixels; coloured text needs the colour added in `ink_bbox`.
- `ScreenCapture` covers overlay canvases; camera canvases need a game-view capture.

## Gotchas (false positives seen)
- The dump must include legacy `UnityEngine.UI.Text` labels, not only TMP; otherwise those buttons look label-less and offsets are reported falsely.
- Never guess the button face by flat colour on gradient sprites: grow the face region along the smooth gradient (neighbour delta below a small threshold) instead.
- Currency pills whose icon deliberately overhangs the frame edge must be skipped (see `ui-currency-bar-contract`), not flagged as off-centre.

## Hidden elements give false positives (lesson 2026-11-04)
The pixel scan reads the screenshot behind a button that is not drawn (alpha 0 / mode off), so it can report a large dx (e.g. -58 px) for a button whose geometry is centred. Before "fixing" a big dx on a conditional button, dump the runtime rects (icon/label world centres vs the button centre). If the geometry is centred, record a false positive; re-run the pixel audit only while the button is visible.
- Notification dots / badges (red dot with a child like `Core`) count as ink in the pixel scan and make "overflow" and dx failures on exactly the tabs that have one. Check whether the failing buttons all carry a dot before changing layout code; mask the dot colour in the pixel script or ignore images under Badge/Dot parents in the dump. A worker "fix" that does not move the measured numbers means the finding was a false positive: revert it.

## Fix at the baked prefab, not only the builder (measured trap)
- Modals/pages that are BAKED prefabs keep their serialized layout values (HLG padding, offsets). Editing the code builder changes only newly built UI: the Play audit shows identical numbers and the fix looks like it "did nothing". Confirm with the audit that the failing object comes from a prefab, then batch-fix the sources with an Editor pass (`PrefabUtility.LoadPrefabContents` -> edit -> `SaveAsPrefabAsset`) AND update the builder so new UI matches. Dry-run first (count objects per sprite/padding), then apply, then re-run the audit.
- Audit numbers that change between captures are animation or test state; only values identical across 2-3 settled captures are real defects. A class of identical offsets (e.g. all tabs -3 px) is one shared fix, not per-screen nudges.

## Glyph side bearings and probe bias (lesson 2026-11-06)
- TMP centres the ADVANCE box of the string, not the drawn glyphs. Side bearings of the first/last glyph (e.g. "S...1", "x3", "28M") push the ink 1-7 px off the rect centre on text-only and icon+price buttons. Fix once at the shared text component: for single-line, centred labels shift the TMP child by the measured glyph-quad ink centre (`textInfo.characterInfo` bottomLeft.x / topRight.x of visible chars, clamp ~12 px), run only when text or layout changes (never per frame).
- Measure ink INCLUDING the dark outline (thicker below): white fill only biases every pair 1-1.5 px up/left.
- Tab-like buttons: take dx on the plate rect and dy on the vertical face run; falling back to the whole rect includes a transparent lip margin and reads a fake dy of about -4.
- Ignore notify dots/badges in the scan; wait for the modal pop-in/slide to settle (30-40 frames) before capturing, otherwise the offset is animation state.
- Prefab text rects baked for one width (landscape chip) spill past the face when the host is narrower (portrait): stretch the label to the live host width with an inset instead of a fixed width.
- Confirm a suspected artifact with a 5x crop and your own silhouette scan before touching layout; keep the audit as a regression gate, not the truth.

- The dump must skip widgets under a CanvasGroup with alpha <= 0.01 (parked/faded buttons) and badge/sticker children (notify dot, x2 sticker): otherwise hidden widgets and overhanging badges show up as fake dx/dy and overlap failures. Name badge children consistently so the dump can skip them.
- Before chasing unstable audit numbers, check whether they repeat: sample the widget several times; a value that changes between runs is a measurement artefact (stale bake, translucent plate over moving 3D), a value that repeats is a real offset. Convert px to layout units from a measured step (e.g. 11 px per 17 units) instead of guessing the sign.
