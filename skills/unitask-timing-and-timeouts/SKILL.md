---
name: unitask-timing-and-timeouts
description: "UniTask timing and timeouts: PlayerLoopTiming choice, Delay vs coroutines, unscaled delays, SuppressCancellationThrow, TimeoutController, WhenAll/WhenAny, UniTaskVoid rules. Use when writing awaits that wait, time out, race or run during pause."
triggers: unitask, delay, timeout, playerloop, timing, whenall, whenany, suppresscancellationthrow, unitaskvoid, async void, await, coroutine, het gio, bat dong bo, huy tac vu, pause
---

# UniTask timing and timeouts

Source: third-party example (Cysharp/UniTask README, MIT) + our practice. Pairs with `async-cancellation` (ownership/CancelToken). Unity 6 also has built-in `Awaitable`; UniTask stays our default (adds WhenAll, DelayFrame, PlayerLoopTiming control).

## When
Any await that waits on time/frames, races two things, must survive `timeScale = 0`, or must not throw on cancel.

## Steps
1. Pick the wait: `UniTask.Delay(ms, DelayType.UnscaledDeltaTime, ...)` for pause menus and reward popups; `DelayFrame(n)`; `Yield()` (no token) is the cheapest next-frame; `WaitUntil` beats polling loops.
2. Pick the timing only when it matters: `PlayerLoopTiming.Update` default; `FixedUpdate` for physics reads; `LastPostLateUpdate` for after-camera work.
3. Always pass a token (see `async-cancellation`). On Unity 2022.2+ `destroyCancellationToken` is the free "owner died" token; link it with the CancelToken for restarts.
4. Hot paths that cancel often: `var (cancelled, _) = await task.SuppressCancellationThrow();` avoids exception cost.
5. Timeouts: reuse one `TimeoutController` field per component instead of a new CancellationTokenSource per call; `op.AttachExternalCancellation(token)` bolts cancellation onto a non-cancellable awaitable.
6. Race/aggregate: `UniTask.WhenAll(a, b)` returns a tuple; `WhenAny` returns the winning index. Cancel the losers explicitly.
7. Fire-and-forget: `async UniTaskVoid` + `.Forget()` (or the project helper). Never `async void` except Unity event callbacks; unhandled errors flow to `UniTaskScheduler.UnobservedTaskException`.

## Pitfalls
- `UniTask.Delay` honours timeScale by default; forgetting `Unscaled` freezes a pause-time popup.
- With domain reload off, static completion sources and caches survive Play: reset them in `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]`.
- Thread-pool work never touches Unity objects; switch back with `await UniTask.SwitchToMainThread()`.
- Async lambdas passed to an `Action` become `async void`: wrap them with `UniTask.Action`.
- WebGL has no threads: do not rely on thread-pool switches there.

## Snippet (our own)
```csharp
TimeoutController _timeout = new TimeoutController();
async UniTask<bool> TryLoad(CancellationToken owner)
{
    var t = _timeout.Timeout(TimeSpan.FromSeconds(5));
    var (cancelled, _) = await LoadAsync(owner, t).SuppressCancellationThrow();
    _timeout.Reset();
    return !cancelled;
}
```

## Verify (Unity MCP)
`console-get-logs` shows no `OperationCanceledException` spam; script-execute a Play test that sets `timeScale 0` and confirms the unscaled delay completes; open the UniTask Tracker window to check no leaked tasks after scene exit.

Details: `references/playerloop-and-awaitable.md`.
