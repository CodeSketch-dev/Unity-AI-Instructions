# PlayerLoop timings and Awaitable comparison (own notes)

Source: third-party example (UniTask README, MIT). API names checked against the Unity C# reference (reference-only licence, no code copied): `MonoBehaviour.destroyCancellationToken` and `UnityEngine.Awaitable` exist in Unity 6.

| Need | Use |
|---|---|
| Next frame | `UniTask.Yield()` / `NextFrame()` |
| N frames | `DelayFrame(n)` |
| Seconds, paused game | `Delay(ms, DelayType.UnscaledDeltaTime)` |
| Condition | `WaitUntil` / `WaitWhile` with token |
| Physics step | `Yield(PlayerLoopTiming.FixedUpdate)` |
| End of frame (screenshots) | `WaitForEndOfFrame()` (no MonoBehaviour needed on 2023.1+) |

Awaitable (Unity built-in) is coroutine-equivalent: no WhenAll, DelayFrame or tracker. Prefer UniTask in game code; use Awaitable only when a library must avoid dependencies; `AsUniTask()` converts.

Tracker: Window > UniTask Tracker lists live tasks; enable stack-trace capture only while debugging (cost).
