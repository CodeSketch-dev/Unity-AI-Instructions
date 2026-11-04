# Two-layer dim (outer blockers + inner shrinking dim)

```
Focus_Pointer (root, size = target size, follows the target)
 +- Top / Bottom / Left / Right      OUTER blockers: children of the ROOT, alpha 0, raycast ON, no Button.
 |                                   Size = target size, so they hug the target rect and never move.
 +- Focus (stretch, offsets tween)   INNER layer
 |   +- Top / Bottom / Left / Right  dim panels: alpha ~0.96, raycast ON, Button (interactable = false while tweening)
 |   +- Pointer (hand)               re-parented under the root focus rect when shown
 |   +- TextMsg                      inactive until a message is set
 +- BtnBlockingFocusBox              stretch to root, alpha 0, Button; raycastTarget switch = pass-through
```

Why two layers
- The inner dim shrinks visually (the hole animation) but may still be mid-tween; the outer blockers already guarantee the whole screen outside the target is blocked from the first frame.
- In pass-through mode the outer blockers still block outside the target (desired) while `BtnBlockingFocusBox.raycastTarget = false` lets the first tap reach the real button through the hole.

Switches
- `dismissOnClickFocusBox`: box button interactable AND `image.raycastTarget = isInteractable`. False = the tap passes through the hole.
- `dismissOnClickOutside`: the four inner dim buttons become interactable. False = the player cannot escape the step (strict steps).
- Any enabled button calls `StopFocus()` then raises the completed event. `OnDestroy` also raises it if still focusing, so callers must tolerate it.
- In strict steps real completion is a game event (for example "worker bought"), which calls `StopFocus(callEvent: false)` and advances the step.
