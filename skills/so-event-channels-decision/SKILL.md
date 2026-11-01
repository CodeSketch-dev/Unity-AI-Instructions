---
name: so-event-channels-decision
description: "Decide between ScriptableObject event channels, StaticBus events and runtime anchor assets for cross-system wiring; SO channels only for designer-wired links. Use when asked to add events, a scene-crossing reference or a decoupled manager link."
triggers: scriptableobject event, event channel, so event, runtime anchor, decouple, listener, static bus vs so, tin hieu, su kien, ket noi
---

# SO event channels vs StaticBus

Source: third-party example (Unity open-project-1, Apache-2.0) analysed; decision rules are our practice. Our default stays `static-bus-events` (typed, code-first, no assets).

## Choose
| Need | Choice |
|---|---|
| Game-wide notification, many subscribers, code-only | StaticBus + IEvent (default) |
| Designer rewires sender/receiver in the Inspector without code | SO event channel (asset with `Raise` + listener component) |
| Persistent manager hands a scene object (player, camera) to other scenes | Runtime anchor SO (`Provide`, `isSet`, `OnAnchorProvided`, cleared in `OnDisable`) |
| One owner, one consumer | Direct reference or C# event |

## Steps if an SO channel is truly needed
1. Generic base `EventChannelSO<T>` with a `UnityAction<T>` event and `Raise(T)`; initialise the delegate empty to skip null checks.
2. Listener MonoBehaviour subscribes in `OnEnable`, unsubscribes in `OnDisable`.
3. Channels live in `Configs/<Feature>/` and are referenced by serialized fields (`scene-authored-prefabs`).
4. Reset runtime state in `OnDisable` so domain-reload-off Editor sessions do not keep stale anchors.

## Pitfalls
- Two parallel buses make flow untraceable: pick one per feature and note it in the feature doc.
- Hidden coupling by asset: Find References In Scene before deleting a channel.
- An anchor read before `isSet` is null: guard or wait for `OnAnchorProvided`.
- open-project-1 loads scenes with coroutines and Addressables; do not copy that into UniTask projects (see `scene-flow-loading`).

## Verify (Unity MCP)
`gameobject-find` the listeners; raise the channel from script-execute in Play Mode and assert receiver state; reopen scene/prefab with no Missing references.
