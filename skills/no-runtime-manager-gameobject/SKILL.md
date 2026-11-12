---
name: no-runtime-manager-gameobject
description: "Use when the linter flags [RULE no-runtime-manager-gameobject] or code builds a manager/system with new GameObject + AddComponent at runtime: replace it with a scene-authored prefab reference."
triggers: new GameObject, AddComponent, DontDestroyOnLoad, runtime manager, tao manager luc chay, lint no-runtime-manager-gameobject
---

# No runtime-built managers

Why banned: the owner vibe-codes and must find and hand-tune every manager in the Hierarchy or Prefab Mode. A manager created by `new GameObject(..)` + `AddComponent<..>()` is invisible there, its tuning lives in code, and it breaks boot order.

## Fix (do these in order)
1. Make the manager a prefab: `Assets/_Game/Prefabs/<Feature>/<Name>.prefab` with the component and its serialized references. Use Unity MCP or the Editor; do not hand-write YAML.
2. Place the prefab instance in the scene, or inside the persistent root prefab when it must survive scene loads (skill `persistent-root-prefab`).
3. Replace the creating code with a `[SerializeField] <Type> _name;` reference (or a static `Instance` set in `Awake` of the prefab's own component). Delete the `new GameObject`, `AddComponent` and `DontDestroyOnLoad` lines.
4. Check: Play 5 s, empty Console, the object is visible in the Hierarchy before Play starts.

## Legit exceptions
Pooled VFX/projectile roots and Editor-only helpers are fine: keep them out of manager code, or add `// lint-ok:no-runtime-manager-gameobject <reason>` on the line. The rule already ignores `Editor/` and `Tests/` folders.

See also: `scene-authored-prefabs` (full prefab-first rules), `persistent-root-prefab`.
