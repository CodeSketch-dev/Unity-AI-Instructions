---
name: house-code-patterns
description: "Use when writing gameplay or system code in the studio house style: Data_, Factory_, _Asset, Event_, state machine, MonoCached owners, pool, collision registry, CancelToken, tween, audio, localization, naming and anti-patterns. Decision table to the leaf templates."
triggers: code patterns, house style, house code, data factory event, owner component, lifecycle, subscribe unsubscribe, cancel token, code style, naming convention, private keyword, underscore field, anti pattern, quy uoc code, kieu code, viet code, kt style, knife tower
---

# House code patterns (SketchEngine first)

Always check the installed package API first (`framework-version-map`); teach and write the SketchEngine form. Translate legacy forms deliberately (`references/v1-to-sketchengine.md`), never mass-replace namespaces. This page is a decision table plus conventions; templates live in the leaf skills and short samples in `references/`.

## 1. Decision table
| Need | Pattern | Leaf skill | SketchEngine type |
|---|---|---|---|
| Saved player state | `Data_<Domain>` block, `DataValue<T>` fields, `??=` in `Init` | `data-block-template` | `SketchEngine.Data.DataBlock<T>`, `DataValue<T>` |
| Authored entry | `<Feature>_Asset : ScriptableObject` in `Configs/<Feature>/` | `config-and-factory-authoring` | plain SO |
| Registry / tuning | `Factory_<Feature>` singleton, static accessors, dictionary in `OnInitialize` | `factory-singleton-template` | `SketchEngine.SO.ScriptableObjectSingleton<T>` |
| Cross-feature notification | `Event_<Feature>_<Noun>_<Verb> : IEvent` | `static-bus-events` | `StaticBus<T>` |
| Runtime mode | enum + state classes + one transition path | `state-machine-template` | `StateMachine<TLabel>`, `IStateMachine` |
| Feature root with parts | root class + `<Feature>_<Part>` siblings | this page | `MonoCached`, `MonoCachedHub<T>`, `MonoCachedFast` |
| Repeated spawn | `PoolPrefabConfig` asset + `PoolPrefabGlobal.Get/Release` | `pool-everything` | `SketchEngine.Patterns.Pool` |
| Triggers / hits | mover is the sensor, world pieces register | `collision-registry` | `OptCollisionSensorFast<T>`, `OptCollisionRegister` |
| Async work | `UniTask` + one `CancelToken` per owner | `async-cancellation` | `SketchEngine.Core.Async.CancelToken` |
| Persistent root, services | scene-authored prefab | `scene-authored-prefabs` | `MonoSingleton<T>` |
| Page + list items | page script on prefab root, item prefab | `ui-page-item-prefab` | `Popup`, `PopupManager` |
| Press feedback, button sfx | components on the prefab | `ui-button-anatomy` | `UIPressPrimeTween`, `AudioButtonSfx` |
| Strings | localize component + factory getter | `localization-pipeline` | project Localization factory |

## 2. Conventions (evidence: counts on the reference project, `references/counts.md`)
- Namespace `Game` for first-party code (92% of files); one top-level type per file, file name == type name.
- Private methods carry no `private` keyword (2274 bare vs 51); fields `[SerializeField] Type _name;` and private `_camelCase` (1563 vs 2); statics `s_name` or `_name`; constants `UPPER_SNAKE`.
- Roles by suffix/prefix: `Data_`, `Factory_`, `Event_`, `<Feature>_Asset`, `<Feature>_Static` (session-only state, plain static class), `_Type` enums, `_Manager`/`_Master` single-instance owners, `_Component` base only when many parts resolve one owner.
- Owners: cache the owner with a `[SerializeField, HideInInspector]` field filled in `OnValidate`; use `MonoCachedHub<T>` (`Hub`) when parts belong to one hub; never repeat `GetComponent` in hot code.
- Population ticking: a single manager or static updater ticks many entities (register in `OnEnable`, unregister in `OnDisable`, reusable removal buffer). Do not give every pickup an `Update`. Check who dispatches `Tick` in the installed `MonoCached` before relying on it.
- Items get data through `Init(config)`; pages refresh in `OnEnable`.
- Lifecycle pairing: bus subscribe/unsubscribe, `OnValueChanged +=/-=`, tween stop, token cancel, pool release all happen in the matching `OnEnable/OnDisable` or `Awake/OnDestroy`.
- Tweens: one library per file; new code PrimeTween (store the `Tween` handle, `Stop()` it in teardown, `useUnscaledTime` for UI). Legacy DOTween sequences stay in place until touched.
- Audio: sfx are `AudioConfig` assets exposed by an audio factory; play with `AudioManager.Play(config)`; never ad hoc `AudioSource` or clip-by-path loading. Every UI button prefab has `AudioButtonSfx`.
- Text: static prefab text uses the localize component; dynamic strings go through the localization factory; pair locale-changed subscriptions.
- Comments and identifiers in English; XML summaries only on public API worth documenting; no `#region` noise.

## 3. Anti-patterns (do not copy even if a reference has them)
See `references/anti-patterns.md`: abstract event class, empty `catch`, raw `GetComponent`/`FindObjectOfType`/`Camera.main` in hot code, leftover raw `OnTriggerEnter`, two tween libraries on one target, `async void`, unbalanced subscribe, `Factory_X.Instance._field` at call sites, unused second pooler, non-English comments.

## 4. Done check
- Each new type matches a row of the decision table; no parallel replacement of a framework type.
- Subscribe/unsubscribe, token, tween and pool pairs are balanced (grep).
- Compile, Console empty, a Play pass that exercises the code path.

## Pitfalls
- Reading a pattern from a legacy project and copying its namespaces: translate, then compile.
- Writing a "template" class that already exists in the package.
- Samples in `references/` are compile-plausible, not copy-paste: verify names against the installed package.

References: `references/samples-data-factory-event.md`, `references/samples-owner-state-pool-collision.md`, `references/samples-async-tween-audio-loc.md`, `references/v1-to-sketchengine.md`, `references/anti-patterns.md`, `references/counts.md`, `references/PROVENANCE.md`.
