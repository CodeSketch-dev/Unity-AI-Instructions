# First-tap verification

## Inspect before changing behavior
In Play, calculate the target's screen-space center using its actual Canvas camera. Use `EventSystem.current.RaycastAll` with a `PointerEventData` at that point; record the first hit, owning raycaster, Graphic.raycastTarget, Button enabled/interactable and ancestor CanvasGroup blocksRaycasts/interactable values. Repeat at the visible fingertip and notice center. A zero-result query is not a passing check.

Expected target-center first hit: the real control or a graphic beneath its same handler hierarchy. A transparent overlay Image, unrelated look pad or unexpected modal is actionable evidence of interception. A disabled Button still intercepts while its Image raycastTarget stays on. A CanvasGroup with blocksRaycasts=false only excludes its own descendants; it does not forward events to unrelated hierarchy branches.

Do not call `Button.onClick.Invoke()` as the test of physical input. That checks only the callback path and bypasses raycasting, pointer release/cancel, press feedback and the input module. Direct handler/unit tests are useful separately and must be labeled that way.

## Play acceptance matrix
Use a temporary action counter on the real target or observe its existing testable result. Never issue repeated real purchases to count events. Back up saves before tests and restore afterwards.

| Gesture/state | Expected action count | Focus result |
|---|---:|---|
| First center down + up | 1 | Completes after accepted action |
| Notice alias down + up | 1 | Same action path, if alias enabled |
| Down then drag/cancel outside | 0 | Stays available |
| Disabled target | 0 | No bypass through alias |
| Inactive/hidden target | 0 | Focus safely hidden |
| Unrelated touch outside | 0 | Outside-dismiss only if configured |
| Two simultaneous touches | <=1 per accepted gesture | No cross-pointer completion |
| Target replaced while pressed | 0 on old target | Old listener detached |
| Hide/disable/destroy/reopen | 0 stale callbacks | Rebind once on new show |
| Hold-only/drag-only target | Owner's accepted-action count | Hold/drag semantics retained |

Test using actual input down/up through the installed Input System/EventSystem, not just reflective method calls. Check target press scale on down/up. Ensure a notice click cannot both fall through to another control and invoke its alias. If a notice is interactive, give it an actual Button and raycaster, and keep its children decorative.

At the end run UI layout/ink checks and inspect supported aspect-ratio screenshots. Report raycast paths, action counts, cancel/disabled outcomes, text containment, hole-to-target dx/dy, audit totals and Console errors. A unit-test pass cannot establish visual or physical-input parity.
