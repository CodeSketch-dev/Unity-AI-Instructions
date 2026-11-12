---
name: unitask-callbacks-and-streams
description: "UniTask bridges: wrap callbacks with UniTaskCompletionSource, await Addressables/UnityWebRequest/AsyncOperation, AsyncReactiveProperty, Channel, async enumerables, button click awaits. Use when turning events or streams into awaitable flow."
triggers: unitaskcompletionsource, callback to async, async enumerable, channel, asyncreactiveproperty, onclickasync, addressables await, unitywebrequest await, awaitable event, doi nut bam, luong su kien
---

# UniTask callbacks and streams

Source: third-party example (Cysharp/UniTask README, MIT) + our practice. Use after `unitask-timing-and-timeouts`. Prefer `static-bus-events` for broadcasts; use these for one-shot "wait until X happens" flow (tutorial steps, popup results).

## Steps
1. One-shot result (popup choice, ad finished): create `UniTaskCompletionSource<T>`, complete it from the callback with `TrySetResult`, `TrySetCanceled` on teardown; return `utcs.Task.AttachExternalCancellation(token)`.
2. Engine async ops: `await op.WithCancellation(token)` for AsyncOperation/UnityWebRequest/Addressables handles; `.ToUniTask(Progress.Create<float>(...))` for loader bars.
3. Wait for a button: `await button.OnClickAsync(token)`; repeated events: `button.OnClickAsAsyncEnumerable(token).ForEachAsync(...)`, cancelled with the owner.
4. Observable value for UI: `AsyncReactiveProperty<int>`; `BindTo(text)` updates TMP/Text and stops with the owner token.
5. Producer/consumer between systems: `Channel.CreateSingleConsumerUnbounded<T>()`; consumer loops over `channel.Reader.ReadAllAsync(token)`.
6. End every loop on the owner token; an enumerable that outlives its scene is a leak.

## Pitfalls
- Use the `Try*` setters; completing a source twice with `SetResult` throws.
- `UniTaskCompletionSource` may be awaited by many callers; `AutoResetUniTaskCompletionSource` is single-await and pooled.
- Addressables handles still need `Release`; awaiting does not free them.
- Do not capture `this` in long-lived lambdas on destroyed objects: guard with the token.

## Snippet (own)
```csharp
UniTaskCompletionSource<bool> _result;
public UniTask<bool> Ask(CancellationToken ct)
{
    _result = new UniTaskCompletionSource<bool>();
    return _result.Task.AttachExternalCancellation(ct);
}
public void OnYes() => _result?.TrySetResult(true);
void OnDisable() => _result?.TrySetCanceled();
```

## Verify
script-execute in Play Mode: open the popup, tap Yes through the EventSystem (`playmode-driver-recipes`), assert the awaiter resumed; close the popup and assert the task is cancelled with no console errors.
