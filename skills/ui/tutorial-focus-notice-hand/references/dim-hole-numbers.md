# Dim-hole technique: exact numbers

Measured on the studio's reference game (prefab YAML, read-only; visual result not observed in Play). Defaults, not law: compare with the target game's screenshots.

## Idea
Four dim panels are anchored to the edges of a `Focus` RectTransform. `Focus` starts expanded by 1000 px per side and its offsets tween to 0, so the dim hole shrinks onto the target. Hole rect = target rect + `extend`.

## Tween
- `offsetMax = +offset * x`, `offsetMin = -offset * x`, `x` from 1 to 0
- offset 1000, duration 0.35 s, ease OutSine, use unscaled time, not auto-killed (reused)
- while the tween runs all buttons are non-interactive; on complete, enable them per option flags

## Panels
| Part | Value |
|---|---|
| Dim colour | black, alpha 0.96 (pointer variant) / 0.98 (message variant); NO sprite (flat colour) |
| Panel size | 3500 x 3500 each |
| Top | anchor (0.5,1), pivot (0.5,0) |
| Bottom | anchor (0.5,0), pivot (0.5,1) |
| Left | anchors (0,0)-(0,1), pivot (1,0.5), width 3500 |
| Right | anchors (1,0)-(1,1), pivot (0,0.5), width 3500 |
| Raycast | all panels raycast ON in the blocking mode; each inner panel also carries a Button (transition None) |
| Box blocker | stretch to root, built-in sliced UISprite, alpha 0, Button; `raycastTarget` toggled for pass-through |

## Hand
| Part | Value |
|---|---|
| Anchor / pivot | anchor (0.8, 0.3) of the target-sized box; pivot (0.1, 0.78) = fingertip |
| Size | 134.3 x 127 (the art is 134 x 127) |
| Icon child | local position (-94, 61); raycast OFF |
| Motion | scale 1 -> 1.1, 0.5 s, linear, yoyo, infinite, restart on enable; never rotates or moves |
| Tuning | caller passes a hand offset, e.g. (0,-25) or (0,70) |

## Message
TMP 36 white (pointer variant) or 32 (message variant), autosize min 18, centred, raycast OFF, project font with outline. Pointer variant: pivot (0.5, 0), placed 4 px above the focus top. Message variant: anchor (0.5, 0) pivot (0.5, 1), 140 px below.

## Targeting modes
ScreenTarget (UI rect; the root follows the target each frame; stop if the target is destroyed), ScreenPoint (fixed), WorldPoint (each frame `WorldToScreenPoint` then `ScreenPointToLocalPointInRectangle` on the overlay canvas; stop when behind the camera). The hole size is set once; only its position follows.

## Pitfalls from the reference
- Both variants duplicate ~200 lines; share a base class in a new project.
- Hole is a hard rectangle (no round or soft mask); no sfx, no skip timeout, no hand rotation logic.
- World-to-canvas conversion that uses the main camera is wrong for camera-space canvases.
- `interactable = false` alone still blocks raycasts; use `raycastTarget` for pass-through.
- A `.gitignore` rule once swallowed the hand sprite; test a clean clone.
- A banner can cover the message: reserve the safe area (banner/native/tutorial conflict was fixed several times).

## Hand.png (shipped in `assets/Hand.png` inside this references folder)
134 x 127 px RGBA, 23,543 bytes. Import: Sprite (2D and UI), Single, 100 pixels per unit, no border, pivot centre, mesh type Tight, mipmaps off, sRGB on, alpha is transparency on, bilinear, clamp, max size 2048, compression quality 50, format Automatic, not readable. The art is the studio's reference asset; reuse follows the target project's asset provenance rules.
