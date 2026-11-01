---
name: ui-visual-qa
description: "Capture a screen at several aspect ratios, diff against a mockup or golden image (pixels, SSIM, edges) and measure text contrast. Use after ui-validator passes or when a build must match a reference image. Part of the ui-always set."
---

# UI visual QA

Order: build (`ui-builder`) -> numeric check (`ui-validator`) -> pixel diff and contrast (this skill) -> fix named regions -> repeat, with an iteration cap (report 17: stop and escalate after 3-5 loops with the same failure signature).

## Capture
Per (screen, aspect) in 1920x1080, 2400x1080, 1600x1200 (+ portrait if the game is portrait): fixed seed, `timeScale 1`, wait for entrance animations (2 frames + tween count 0 or ~1 s unscaled), same fonts, freeze particles/animated backgrounds, lossless PNG into `qa/artifacts/`. Preferred: the Editor capture template `assets/Qa_Capture.cs.txt` (UNCOMPILED; `Qa_Capture.CaptureAll(prefabPath, outDir, sizes)` renders through a ScreenSpace-Camera canvas into a RenderTexture at exact sizes). Fallback: the MCP Game-view screenshot (resolution follows the Game view window; costs tokens, so view only crops). The reference image is captured at 1920x1080 only; other aspects are covered by rules and by golden regression (first approved capture per aspect in `qa/golden/<aspect>/`).

## Diff
`py -I <skills>/ui-visual-qa/scripts/image_diff.py ref.png actual.png [--mode mockup|golden] [--mask qa/masks/<screen>.json] [--out diff.png]`
- Pixel differs if any RGB channel is off by more than 12/255. Same-size images required. Masks `[[x0,y0,x1,y1],...]` hide timers and random rewards.
- Metrics: differing pixel %, block SSIM (8x8 grayscale), Sobel edge-map mismatch with 1 px tolerance (catches shifted frames when colours are alike; images are downscaled to ~480 px for it).
- Verdicts (initial thresholds): mockup PASS needs pixels <= 1.5%, SSIM >= 0.97 and edge mismatch <= 15%; WARN up to 4% / 0.93 / 30%; the worst metric wins. Golden uses pixels only: PASS <= 0.2%, FAIL > 1%. A 1920x1080 diff runs in about 1 s.
- Output lists the top regions with boxes and pixel counts; map a box to an element via the validator rects to make the fix exact. Look at the diff crop of the top 2 regions, never repeated full-resolution images (token cost).

## Contrast
`py -I ui_validator.py screen.prefab --dump-rects texts.json` then `py -I <skills>/ui-visual-qa/scripts/ui_contrast.py screenshot.png texts.json [--min 3.0] [--strict]`. Each text rect is split into two luminance clusters (2-means) and the WCAG ratio is printed; below 3:1 is a WARN (exit 1 only with `--strict`). The screenshot must show the same aspect the rects were computed for.

## Calibrating the thresholds (needs real screenshots; not done yet)
The numbers above are starting values. Before enforcing them as a gate: capture 5 approved screens at 3 aspects, re-capture after a deliberate 1-2 px shift, a font change and a colour tweak, record the three metrics for "same", "acceptable" and "wrong" pairs, then set PASS/WARN/FAIL between the observed groups and write the values into the project's `qa/ui-thresholds.json`. Until then the verdicts are advisory.

Limits: only 8-bit non-interlaced PNG; the Editor capture template was not compiled (no Unity MCP this session); a mockup that was not rendered by Unity will always differ in antialiasing and fonts. Taste decisions (look, feel) stay with the user.

## Popup capture batches
Snapshot popup-root children before create, destroy only the new ones after capture, wait for the open tween, and claim blocking popups (offers, offline reward) with a real tap first; they respawn on resize/focus.

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.
