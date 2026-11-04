---
name: static-bus-events
description: "Use when many unrelated systems must react to one notification: define IEvent classes, Post, symmetric Subscribe/Unsubscribe, handler naming, folders, test-bus filtering, asmdef reference. Not for a single owner talking to its own children."
triggers: static bus, staticbus, event, ievent, post, subscribe, unsubscribe, observer, notification, event class, su kien, phat su kien, dang ky su kien, huy dang ky, kt style, knife tower
---

# StaticBus events (SketchEngine form)

`StaticBus<T>` (namespace `SketchEngine.Patterns.Observer`, assembly `SketchEngine.Patterns`) is a per-type static delegate: synchronous, no queue, only the event object allocates. Check the installed package API first.

```csharp
using SketchEngine.Patterns.Observer;
namespace Game
{
    public class Event_Character_Dead : IEvent
    {
        public Character Character { get; private set; }
        public Event_Character_Dead(Character character) { Character = character; }
    }
}
// post:      StaticBus<Event_Character_Dead>.Post(new Event_Character_Dead(this));
// listen:    StaticBus<Event_Character_Dead>.Subscribe(StaticBus_Event_Character_Dead);
```

## Rules
1. Folder `Scripts/Event/<Feature>/`, one class per file, name `Event_<Feature>_<Noun>_<Verb>`, payload via constructor, get/private-set properties. Classes, not abstract (an `abstract` event cannot be posted).
2. Subscribe and Unsubscribe are symmetric in the matching lifetime: `OnEnable/OnDisable` for active-only listeners, `Awake/OnDestroy` for object-lifetime listeners. A destroyed listener left subscribed throws `MissingReferenceException` on the next Post and, with domain reload off, survives Play sessions.
3. Handler name `StaticBus_<EventName>(Event_X e)` (or `OnX`), matching nearby code.
4. Use it for cross-feature or many-to-many notifications. One owner and its own children use a direct reference or a C# event (`Action`). Pure logic classes driven by unit tests may keep plain C# events.
5. Never Post in per-frame paths (allocates an event each call); never use the bus inside a shared package.
6. Statics tied to subscriptions registered in `RuntimeInitializeOnLoadMethod` are reset at `SubsystemRegistration`.
7. Add `SketchEngine.Patterns` to every asmdef that posts or subscribes (only when the project has asmdefs).
8. Several instances of one facade in tests: events carry `object Source` and tests subscribe through a source-filtering test bus that unsubscribes at the next test start (static buses leak between tests). Templates: `unity-script-migration/templates/`.

## Done check
- `grep` of `Subscribe(` vs `Unsubscribe(` in the touched files is balanced per class.
- Every event class has a Post site and at least one subscriber (otherwise delete it).
- Play 5 s, Console empty, destroy the listener scene object and Post once: no exception.

## Pitfalls
- Subscribing in `Awake` without an `OnDestroy` unsubscribe (common in legacy code, do not copy).
- Handler lambdas cannot be unsubscribed; use named methods.
- Events used as a command channel for one receiver: replace by a direct call.

Audit unbalanced pairs: `py -I <skills>/framework-version-map/scripts/framework_inventory.py <project>`. References: `references/counts-and-provenance.md`.
