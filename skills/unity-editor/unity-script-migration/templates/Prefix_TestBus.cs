using System;
using System.Collections.Generic;
using NUnit.Framework;
using SketchEngine.Patterns.Observer;

// Replace {{Namespace}} and {{Prefix}}. Rename the file to <Prefix>_TestBus.cs.
namespace {{Namespace}}.Tests
{
    // Test helper for StaticBus events: subscribes only to events raised by one source instance and unsubscribes everything
    // automatically when the next test starts (a static bus would otherwise leak handlers between tests).
    public static class {{Prefix}}_TestBus
    {
        static readonly List<Action> _unsubscribe = new List<Action>();
        static string _testId;

        public static void On<TEvent>(object source, Action<TEvent> handler) where TEvent : IEvent, I{{Prefix}}_Source
        {
            string id = TestContext.CurrentContext.Test.ID;
            if (id != _testId)
            {
                Clear();
                _testId = id;
            }
            Action<TEvent> filtered = e =>
            {
                if (ReferenceEquals(e.Source, source)) handler(e);
            };
            StaticBus<TEvent>.Subscribe(filtered);
            _unsubscribe.Add(() => StaticBus<TEvent>.Unsubscribe(filtered));
        }

        public static void Clear()
        {
            for (int i = 0; i < _unsubscribe.Count; i++) _unsubscribe[i]();
            _unsubscribe.Clear();
        }
    }
}
