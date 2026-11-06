---
name: tutorial-focus-notice-hand
description: "Use when a tutorial spotlight, pointing hand, notice or quest-focus overlay needs visual parity or the highlighted button misses its first tap. Covers focus-hole geometry, real click delivery and measured Play checks."
triggers: kt style, knife tower, tutorial hand, dim hole, tutorial, ftue, spotlight, focus pointer, quest focus, quest_focus_message, quest_focus_pointer, pointing hand, notice tap, onboarding, huong dan, ban tay, bam giua, khong onclick, khong bam duoc
---

# Tutorial focus, hand and notice

Apply automatically to onboarding spotlights, focus messages, pointing hands and first-tap failures. Read `ui-always` and its required UI set before editing a view. Use project rules for gameplay steps and wording; keep those decisions out of this shared skill.

## 1. Inspect and select the reference profile
1. Confirm the connected Editor's project path, target scene, input module and existing focus prefab before mutation.
2. Read the target's actual Button/custom control, focus raycaster, CanvasGroups and presenter. Inspect the requested reference through its MCP when available; use the dated archive only as fallback and state that limitation.
3. Use the [reference profile](references/reference-profile.md) for the default shrink-hole/hand style. Record deliberate local deviations in project docs. A softer dim, shifted fingertip, extra gold rings or different notice position is a deviation, never silently called 100% parity.
4. Treat [historical evidence](references/README.md) as snapshots. Do not copy their project contracts, class names, save dependencies or old raw-input behavior into a new project.

## 2. Author the complete view
1. Ruling: the focus overlay is a **scene-authored prefab** placed (inactive by default) under the persistent popup canvas's overlay container inside the persistent root prefab (`persistent-root-prefab`); runtime only shows it, fills data (target rect, message, hand offset) and hides it. Bake the focus box, four dim panels, hand and notice into that source prefab; keep references and tuning serialized. Never build the hierarchy at runtime. The reference game spawns the pointer/message prefabs lazily from a prefab factory and destroys them on dismiss (one allocation per step); that is its single deliberate exception for a persistent overlay singleton, not the recommended form. Spawning a prefab reference is acceptable only if a scene-placed copy is impossible.
2. Size the box from the target control's own rect, excluding decorative icon overhang. Convert corners through the actual target/overlay cameras; world corners are screen pixels only for overlay canvases.
3. Animate the hole's offsets toward zero using unscaled time. Follow a moving target without restarting the appear tween every frame. Keep the hand orientation fixed; yoyo only its scale around the fingertip pivot.
4. Put the dim first and hand last in the overlay, as the last sibling of the overlay container each time it is shown. Sort above the intended popups and below global fades (the reference uses the popup canvas's overlay container, i.e. the same canvas as popups but last sibling; transition canvas above). Keep notice content clear of the hand, target text, safe area, banners and native ads.
5. Build notice icon + localized text as one centered HorizontalLayoutGroup with automatic fitting and outlined Capline text. For a clickable notice reuse the project's Button press feedback and sfx.
6. Save and re-read the source prefab's actual serialized values and a scene instance. Changing a C# default does not migrate existing prefab tuning; update through an Editor migration/builder, preserving field names and unrelated overrides.

Technique numbers (hole tween, panel sizes, alpha, hand, two-layer blockers): [dim-hole-numbers](references/dim-hole-numbers.md) and [two-layer dim](references/two-layer-dim.md). Step driver and world arrow: [step-driver](references/step-driver.md), [quest-arrow](references/quest-arrow.md).

## 3. Deliver the first tap to the real action
1. In pass-through mode disable `Graphic.raycastTarget` on every decorative image/text and any transparent center blocker. A disabled Button can still block raycasts; `interactable = false` does not make its Image transparent to input.
2. Let the real target own pointer down/up/click and press feedback. Observe its actual `onClick` to dismiss the focus; a raw pointer-down inside a rectangle is not action completion. Preserve cancel, drag, multitouch and disabled semantics.
3. Bind a cached listener once per target/lifetime; unbind on target replacement, hide and disable/destroy. Do not allocate listeners or reactivate an already dismissed canvas every frame.
4. A notice alias dispatches the same active, interactable target action once on a completed click. Never duplicate purchase, reward, spend or progression code; never invoke again after the EventSystem already delivered the target click.
5. For a custom hold/drag control observe its real accepted-action event. Do not replace a held action with a synthetic one-shot `Button.onClick`. If forwarding through a blocker is required, route down/up/click together using the project's existing forwarding path and prevent a second pass-through delivery.
6. Use [input verification](references/input-verification.md) to identify the real top raycast hit before blaming the overlay. Do not claim a blocker was found from static code alone.

## 4. Verify before reporting
- Run relevant EditMode regression tests, compile, inspect missing references and Console errors.
- In Play record `EventSystem.RaycastAll` at the target center and notice center, then send a real down/up sequence through the project's input module. Action counter: first completed target tap = 1; notice alias = 1; disabled, canceled or unrelated tap = 0.
- Test replacing/hiding/destroying the target, a moving target, reopening the tutorial, a popup above it and custom hold behavior. Restore test saves after QA.
- Measure focus-hole center/size vs target (<=1 px) and notice group centering/text containment; run the UI layout/ink audit and inspect screenshots at supported aspect ratios. Compare hand, dim and tween against the selected reference.
- Report skills read, source prefab paths, measured dx/dy, action counts, audit totals, PASS/SKIP counts and any device/reference limitation. No Play measurement means visual/input parity remains unverified.

## Routing examples
- "The tutorial hand is different and tapping the middle does nothing": load this skill + UI set; inspect reference and raycast hit; verify one real action.
- "A notice should trigger the focused buy button": reuse its guarded action and test disabled/canceled taps without duplicating spend logic.
- "The hand moves onto the label": measure target rect and fingertip/profile before changing anchors.
- "Change the app icon horse silhouette": do not route here; use art/image skills.

## Off-screen targets (measured trap)
A spotlight on a world point that is outside the screen leaves the four dim panels covering only part of the screen (L-shaped hole). Clamp the focus centre inside the canvas, widen the Top/Bottom panels (12000), re-clamp the message inside the canvas every frame, and for a target outside the viewport show a text hint instead of a spotlight.

## Scene-authored overlay traps (verified in Play)
- If the focus prefab is placed in the scene under its own overlay canvas, the code that reparents the instance (`SetParent(_canvasRect)`) must resolve `_canvasRect` from THAT canvas before any HasInstance early-out; a null canvas silently detaches the instance to the scene root and it stops rendering while `IsFocusing` still returns true.
- Check by script, not by the flag: `instance.transform.parent` must be the overlay canvas and a Play screenshot must show the dim + hole + hand.
- Clamp the message with the RENDERED text bounds (`textBounds`), every frame while the target is a UI element at a screen edge; the text rect is often narrower than a no-wrap line.
- Never freeze with `Time.timeScale = 0` to screenshot a tween-driven overlay: scaled-time tweens never start and the overlay stays invisible.
