---
name: async-cancellation
description: Own UniTask work with CancelToken so it stops on disable, destroy or restart. Use when writing delays, waits, loops or loads that can outlive their owner.
---

# Async cancellation

`CancelToken` wraps a `CancellationTokenSource`: `Token` creates the source lazily; `Cancel()` cancels, disposes and nulls it so the next `Token` is fresh (report 01, VERIFIED).

```csharp
CancelToken _cancel = new CancelToken();
async UniTaskVoid Run()
{
    _cancel.Cancel();                                   // cancel the previous run first
    await UniTask.Delay(1000, cancellationToken: _cancel.Token);
}
void OnDisable() => _cancel.Cancel();
```

## Rules (house style; policy INFERRED, tool facts VERIFIED)
- Every async operation whose owner can be disabled, destroyed or restarted has a cancel strategy; cancel in the matching teardown callback.
- Pass `.Token` to every delay, wait, loop and load.
- Never cache `Token` across a `Cancel()`: it is a stale cancelled token. Read it fresh.
- `UniTaskVoid`/`async void` only for deliberate fire-and-forget; use the project's helper to log exceptions.
- Unity API stays on the main thread: no `Task.Run` for gameplay.
- Prefer an event or `WaitUntil` with cancellation over polling every frame.
- Also kill owned tweens and return pooled objects in the same teardown.

## Added from UniTask (2026-11-02)
Source: third-party example (Cysharp/UniTask, MIT). Timing, timeouts and no-throw cancel: `unitask-timing-and-timeouts`; callbacks and streams: `unitask-callbacks-and-streams`.
