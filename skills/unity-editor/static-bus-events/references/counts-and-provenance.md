# Counts and provenance

Measured on the studio's Knife Tower style reference (an older CodeSketch v1 build; same concept, namespace `CodeSketch.Patterns.Observer`):
- 65 event classes, all `class : IEvent`, spread over about 20 `Event/<Feature>` folders.
- 121 `Post`, 131 `Subscribe`, 130 `Unsubscribe` calls (one unbalanced site: do not copy).
- Handlers mostly named `StaticBus_<Event>`; 1:1 owners keep C# events (`Character.EventDead`, `IAPManager.OnProductsFetched`).
- Counter-example found: an `abstract` event class (cannot be posted), a bus used for a single-owner detail, a new event object per hot Post.
New work uses SketchEngine: `SketchEngine.Patterns.Observer.StaticBus<T>` and `IEvent` (verified in the installed package: `Subscribe(Action<T>)`, `Post(T)`).
