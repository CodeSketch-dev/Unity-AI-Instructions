---
name: static-bus-events
description: Define and use StaticBus events (IEvent classes, Post, Subscribe/Unsubscribe pairing). Use when many unrelated systems must react to one notification.
---

# StaticBus events

`StaticBus<T>` is a per-type static delegate: synchronous, no queue, only the event object allocates (report 01, VERIFIED).

```csharp
public class Event_Character_Dead : IEvent
{
    public Character Who { get; private set; }
    public Event_Character_Dead(Character who) { Who = who; }
}
StaticBus<Event_Character_Dead>.Post(new Event_Character_Dead(this));
```
Files: `Scripts/Event/<Feature>/Event_<Feature>_<Action>.cs`.

## Rules
- Subscribe/Unsubscribe symmetric in the matching lifetime: `OnEnable`/`OnDisable` for active-only listeners, `Awake`/`OnDestroy` for object-lifetime ones. A destroyed listener left subscribed throws `MissingReferenceException` on the next Post and, with domain reload off, survives Play sessions.
- The reference code does not always follow this (knife-tower `AI.cs` subscribes in `Awake` without unsubscribing); do not copy that.
- Handler name: `StaticBus_Event_X` or `OnX`, matching nearby code.
- Use it for cross-feature or many-to-many notifications. A single owner talking to its own children should use a direct reference or C# event.
- Avoid Post in per-frame paths (allocates an event each call); never use it inside a shared package.
- Reset any statics tied to subscriptions at `SubsystemRegistration` if you register in `RuntimeInitializeOnLoadMethod`.

Audit unbalanced pairs with `py -I <skills>/framework-version-map/scripts/framework_inventory.py <project>`.
