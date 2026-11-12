---
name: no-find-in-update
description: "Use when a C# file with Update, FixedUpdate or LateUpdate calls FindObjectOfType, FindObjectsOfType, FindFirstObjectByType, FindAnyObjectByType or GameObject.Find: cache the reference once, never scan the scene per frame (low-end Android hitch)."
triggers: FindObjectOfType, FindObjectsOfType, FindFirstObjectByType, GameObject.Find, Update hitch, per frame find, scene scan, tim kiem moi frame, hitch update
---

# No scene search inside per-frame code

Why: `FindObjectOfType` / `GameObject.Find` walk the whole loaded scene. Called from `Update` (or `FixedUpdate` / `LateUpdate`) on every enemy or pickup, they cost a frame spike on low-end Android and show up as hitches in the profiler.

## Fix steps
1. Find the target you are searching for. Prefer a serialized reference assigned in the prefab (`[SerializeField] Transform _target;`), so the scene is never searched.
2. If the target is spawned at runtime, get it from the owner that creates it (factory, manager, event with the payload) and store it in a field when it arrives.
3. If you must look it up once, do it in `Awake` / `Start` / `OnEnable` and keep the result in a field. Never repeat the call in the per-frame method.
4. Verify: the per-frame method has no `Find*` call; in Play, the Profiler `Scripts`/`GC Alloc` rows for the enemy or pickup stay flat over 10 s.

## Legit exceptions
- A one-time cache in `Awake` / `Start` inside a file that also has `Update`: the rule flags the line because it cannot tell which method it is in. Keep the cache and add `// lint-ok:no-find-in-update <reason>` on that line. Do not add the opt-out to a line inside `Update`.
- Editor-only tools and tests are excluded by the linter already.

## Verification
- `python .claude/lint/run_lint.py --changed` reports no `[RULE no-find-in-update]`.
- Play Mode: no hitch from the affected object, see the `profiling-evidence` and `mobile-perf-audit` skills for the measurement.
