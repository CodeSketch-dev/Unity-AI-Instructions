# Anti-patterns found in reference projects (do not copy)
1. `abstract` event class (cannot be posted); bus used for a single-owner detail; new event object per hot Post.
2. Empty `catch { }` around per-frame calls (swallows errors).
3. Raw `GetComponent` (495 calls), `FindObjectOfType` family (19), `Camera.main` (15) outside setup.
4. Leftover raw `OnTriggerEnter/OnCollisionEnter` (16/3) beside the registry.
5. Two tween libraries on one target; unkilled sequences; capturing lambdas in hot tweens.
6. `async void` (4), coroutines mixed with UniTask, polling timers in `Update`.
7. Subscribing in `Awake` with no unsubscribe.
8. `Factory_X.Instance._field` from call sites instead of static accessors; LINQ over configs per frame; silent `_dict[id] =` overwrite.
9. A second pooler (`PrefabPooler`, `PoolPrefabShared`, ad hoc stacks) with 0 usages.
10. `Update` on every item/pickup; debug input outside `#if UNITY_EDITOR`.
11. File/class mismatches, typos in names, non-English comments, `using UnityEditor` in runtime code.
12. `Data_X.Get` using `ContainsKey` + assignment instead of `TryAdd`.
