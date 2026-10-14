# HUD zone coordinates and sizes

Contents: Reference resolutions, Anchor presets per element, Sizes, Margins, Rails, Test matrix, Common mistakes.

## Reference resolutions
- Portrait: 1080 x 1920. Landscape: 1920 x 1080. Canvas Scaler = Scale With Screen Size.
- Unity Match: start at 0.5; for portrait games whose layout is width-bound set 0 (width) and verify tall phones; for landscape consider 1 (height) and verify ultrawide.

## Anchor presets (anchor = pivot = the corner/edge named)
| Element | Anchor/pivot | Offset from edge (ref px) | Size (ref px) |
|---|---|---|---|
| Settings gear | top-left | 40 / -40 (down) | 110 |
| Level / progress bar | top-center | y -40 | 520 x 90 |
| Currency bar(s) | top-right | -40 / -40 | 340 x 90 each, 12 gap |
| Left rail (daily, events, offers) | top-left | x 40, y -170 | 120 each, 16 gap, vertical |
| Right rail (shop, pet, backpack) | top-right | x -40, y -300 (below currency) | 120 each, 16 gap, vertical |
| Joystick area | bottom-left | 0 / 0, covers left 45% x lower 60% | outer ring 260-320, handle 110-140 |
| Primary action | bottom-right | -60 / 140 | 200-240 |
| Jump | bottom-right | -300 / 250 | 150-180 |
| Secondary skills | bottom-right arc | around the primary, radius ~260 | 120-140 |
| Hotbar | bottom-center | y 60 | slot 120, 8 gap |
| Zone banner | top-center | slides from y +200 to -160, 0.35 s, hold 2 s, fade 0.4 s | 700 x 160 |
| Toast stack | top-center below progress | y -180 | 600 x 80 each |

Landscape: use the same corners; the usable height is smaller, so shrink rails to 96-104 px or use two columns. Keep the joystick in the left third and actions in the right third.

## Sizes
- Minimum interactive: 120 px (about 48 dp at 1080 px width). Primary: 200+. Spacing: 24+.
- Text: body >= 36 px, labels >= 28 px; outline or shadow for legibility over the world.
- Icon in a button: 55-65% of the button diameter.

## Margins and safe area
- HUD root = SafeArea rect. Additional 24-40 px margin inside the safe area.
- iOS home indicator: keep bottom-center elements >= 34 pt above the bottom edge (SafeArea covers it).
- Android gesture bar: same rule; do not rely on fixed values.

## Rails
- Max 5 items per rail; overflow goes to a "more" popup.
- Order by importance from the corner outward; badges at the top-right of each icon.
- Unlock progressively; hidden buttons must not leave gaps (use a layout group that collapses).

## Test matrix (Game view)
| Ratio | Example device | What to check |
|---|---|---|
| 9:16 | older phones | baseline |
| 9:20 | modern tall phones with notch | safe area, tall space, rails not too low |
| 3:4 | tablets | elements not stretched; joystick and actions not too far apart |
| 16:9 / 20:9 landscape | if supported | vertical space, rails |

## Common mistakes
- Anchoring everything to center, then it floats away on other ratios.
- Stacking Attack, Pick up and Drop as separate buttons (they should share one slot).
- Joystick area overlapped by a full-screen invisible UI image that eats touches.
- Placing the currency under the notch (outside safe area).
- Forgetting the largest state of swapping buttons when testing overlap.
- Mirrored text from negative scale on world-space UI.
