# Step driver pattern

The focus overlay has no step data of its own. The owner (one tutorial MonoBehaviour per game mode) holds the steps.

- Steps: `const int STEP_*` in the owner; a switch in `CheckAndProcess()`.
- State: `DataValue<int> TutorialPhase` and `DataValue<bool> IsTutorialCompleted` in the owning feature's Data block (no global tutorial block). A tutorial object destroys itself in `Awake` when completed.
- Waypoints: a small marker MonoBehaviour with a static `Dictionary<int, Transform>` registry, one per world location; a HUD hint line component for text.
- Texts through the localization facade; never literals.

```csharp
// strict "tap this button" step
static void FocusOnButton(RectTransform target, string message, Action onCompleted) =>
    TutorialFocus.Focus(new FocusOptions {
        mode = TargetMode.ScreenTarget, uiTarget = target, message = message,
        showMessage = true, showHand = true,
        dismissOnClickFocusBox = false, dismissOnClickOutside = false, onCompleted = onCompleted });

// advance on the real game event, not on the overlay
void StaticBus_WorkerBuy(Event_Worker_Buy e)
{
    if (TutorialPhase.Value != STEP_BUY_WORKER) return;
    TutorialFocus.StopFocus(callEvent: false);
    NextStep();                                   // TutorialPhase.Value++; CheckAndProcess();
}
```

Rules
1. Wait until the target button is active before focusing.
2. Guard re-entry: `if (TutorialFocus.IsFocusing) return;`. Other systems poll `IsFocusing` (camera pinch zoom, duplicate guards) so gameplay input pauses while a step is up.
3. `StopFocus(false)` on popup close and scene exit; unsubscribe from the bus in `OnDestroy`.
4. Awaited world-point message: `Focus...(onFocusCompleted: () => closed = true)` then `await UniTask.WaitUntil(() => closed, cancellationToken: token)`.
5. Monetization reads the same completed flag (rating, native ads, IAP entry popups, ads break).
6. One reusable overlay for all modes: the reference rebuilt a tutorial per mode and spent nine fix commits in two days.
