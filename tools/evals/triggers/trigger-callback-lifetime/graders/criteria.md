---
type: llm
weight: 1
---

The agent reads the existing lifecycle/subscription guidance first; explains that removing a listener does not invalidate a callback already captured or queued; guards callbacks against inactive lifetime and current binding generation plus source identity (including same-source rebind); and proposes tests that invoke captured callbacks after disable and after rebind without allowing stale state changes.
