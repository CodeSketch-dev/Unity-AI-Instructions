---
name: tutorial-focus-notice-hand
description: Use when building or fixing a tutorial / FTUE focus layer (Quest_Focus_Pointer style): dim overlay with a hole that shrinks onto the target button, pointing hand with fingertip pivot, black notice frame, ground arrow. Exact values, hierarchy dumps, a portable script and screenshots are in references/.
triggers: tutorial, ftue, focus, hand, pointer, notice, onboarding, quest focus, quest arrow, huong dan, ban tay, thong bao, tutorial focus
---

# Tutorial focus layer (owner-approved, ported from a shipped game's Quest_Focus_Pointer)

Everything an agent needs is in this folder. Do NOT look for the original project: the numbers are in `references/prefab-dumps/`, the art in `references/assets/Hand.png`, screenshots of the approved look in `references/images/`, a portable script in `references/reference-implementation/QuestFocusPointer.template.cs.txt` and full in-game examples (with their project dependencies) next to it.

## 1. What the layer is (four parts, nothing else)
1. **Focus pointer** = a dim overlay whose HOLE is the target button, plus the hand. Its own overlay canvas (sort about 310: above popups at 300, below fades).
2. **Notice / focus message** = ONE short word (+ icon) in a translucent black rounded frame (or a Steal/Break style ribbon). Never a blue "tap me" button look.
3. **Focus ring** (gold, optional) pulsing on the target.
4. **Ground arrow** for walking: a `LineRenderer` (see `references/prefab-dumps/Quest_Arrow.prefab.txt` and `M_Quest_Arrow.mat.txt`): 2 points (0,0,0) -> (0,0,10), world space, width 1, texture mode Stretch, scrolling arrow texture material (transparent, cull off, ZWrite off, `_Speed 4`, `_Length 4`, base colour red). Script params: reach threshold 0.5, start/end offset 0, local scale 1, use lowest Y = true. Shown only while the target is far.

## 2. Focus pointer hierarchy (exact values; full dump in `references/prefab-dumps/Quest_Focus_Pointer.hierarchy.txt`)
```
Quest_Focus_Pointer      centre anchors, 325 x 125, script params _offsetValue = 1000, _duration = 0.35 (ease OutSine)
 |- Top/Bottom/Left/Right  (root level, alpha 0 blockers, same geometry as below)
 |- BtnBlockingFocusBox    stretch, Image alpha 0 + Button (not interactable): swallows a tap on the box when enabled
 '- Focus                  stretch (0,0)-(1,1)   <- its offsetMin/offsetMax are ANIMATED
     |- Top     anchor (0.5,1)(0.5,1)  pivot (0.5,0)   size 3500 x 3500   black a=0.96
     |- Bottom  anchor (0.5,0)(0.5,0)  pivot (0.5,1)   size 3500 x 3500   black a=0.96
     |- Left    anchor (0,0)(0,1)      pivot (1,0.5)   size 3500 x 0      black a=0.96
     |- Right   anchor (1,0)(1,1)      pivot (0,0.5)   size 3500 x 0      black a=0.96
     |- TextMsg anchor centre, pos (0,-100), 400 x 150, white TMP 36 (auto 18..72), centre / top, inactive by default
     '- Pointer  anchors (0.8,0.3)(0.8,0.3)  pivot (0.1,0.78)  size 134.35 x 127
          '- Icon = Hand.png, same anchors/pivot, preserveAspect, raycast off,
             scale animation 1 -> 1.1, 0.5 s, yoyo, loop forever
```
Behaviour (Focus(target) API): the root is placed at the target centre and sized to the target's OWN rect (+ optional extend), NOT to its overhanging icon. Show tween: `v` goes 1 -> 0 over 0.35 s OutSine and sets `Focus.offsetMax = +offsetValue * v`, `offsetMin = -offsetValue * v` (the hole shrinks onto the button); the message fades in over 0.3 s. The hand is reparented under the root with `anchoredPosition = handOffset` (default 0), scale 1. The message sits just above the focus top (pivot (0.5,0), +4 px). Tapping the box (blocking button) or outside (close buttons) stops the focus; the root follows the target every frame.

Hand sprite: `references/assets/Hand.png` (134 x 127). It points UP-LEFT: the index fingertip is near the top-left corner, which is why the pivot is at the fingertip: owner-verified (0.08, 0.82), original (0.1, 0.78). **Never rotate, mirror, sway or move the hand.** Same orientation on every button. The only animation is the scale yoyo, which zooms around the fingertip because the pivot is the fingertip. See `references/images/hand-inspector-owner-values.webp` for the owner's Hand inspector values.

## 3. Owner decisions for the game port (deliberate deviations from the original)
- Dim alpha 0.6 (original 0.96) and `raycastTarget = false` on the dim panels: children must still walk and dig while the tutorial points at a button. Use blocking only for popups.
- Hand anchors `(0.7, 0)` of the focus box (original 0.8 / 0.3): wide rail buttons carry the label across the whole plate, so 0.25 to 0.3 lands on the text; y = 0 puts the fingertip on the bottom edge, below the text (tune the serialized field). x about 0.7 keeps it right of the icon.
- The hand is the LAST sibling of the overlay (never behind the ring, the message or any UI); the dim box is the FIRST sibling.
- Notice (focus message): translucent black frame alpha about 0.85, icon + ONE word (kids-first, localized), about 150 px wider than the text so it is easy to notice, high on screen: beside a top-edge button level with it; above a right-side action button (e.g. "HOLD TO DIG!" above the dig disc). Never in the middle of the screen, never covered by the hand. It may be tappable as an alias of the target.
- A far target needs a reachable button: reveal the travel button during that step (a "needs travel button" flag read by the HUD visibility rule), then point at it.
- Positions are fixed fractions (anchorMin = anchorMax), never animated; only scale animates.

## 4. Build recipe (any Unity project)
1. Copy `Hand.png` (import as Sprite, no mipmaps) and `QuestFocusPointer.template.cs.txt` as `QuestFocusPointer.cs` (compiles standalone: uGUI + Input System; adapt if the old input manager is used).
2. Create it once under the HUD canvas root with `QuestFocusPointer.Create(canvasTransform, handSprite)`. For scene-authored prefab rules bake it as a prefab (hierarchy of section 2) and place it in the scene; keep tunables as `[SerializeField]`.
3. Call `Show(targetRect)` / `Hide()` from the tutorial flow. The target must be the button's own RectTransform (the plan rect), not a child icon.
4. Add the notice (focus message) as a second small component: black rounded plate, icon + word, pop-in 0.3 s OutSine, placed per section 3. `references/reference-implementation/Quest_FocusMessage.dig-for-egg.cs.txt` and `Ftue_KtPresenter.dig-for-egg.cs.txt` show one finished version (placement rules, tap on notice, DIG-above-button rule).
5. Verify in Play at 1920x1080: (a) the hole is on the button, (b) the fingertip touches the bottom edge and covers no text, (c) the dim does not block walking, (d) the hand yoyo scales in place. Compare with `references/images/final-dig-site-dim-hole-hand-notice.png`.

## 5. Pitfalls we hit
- Unity keeps SERIALIZED values of a component that already exists in a scene or prefab: after changing a field default in code the old value still applies. Rename the field (new serialized name) or use consts when you change a default.
- Do not position the hand from code every frame with computed offsets (it looked like it "moved around"); anchors inside the box + pivot on the fingertip is the whole trick.
- Sizing the box from the visible-bounds union (plate + overhanging icon) put the hand off the plate; use the target's own rect.
- The Editor runs the game slowly while its window is unfocused: the first seconds may show only the notice before the button appears.
- Tests that assert English literals of tutorial words must be updated with the key; localized files need a font re-bake for new glyphs.
- The overlay must be above every popup: same overlay canvas, last sibling for the hand, sort order above popups.
