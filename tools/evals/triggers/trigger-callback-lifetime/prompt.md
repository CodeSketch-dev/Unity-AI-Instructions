---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

A Unity listener unsubscribes when disabled, but a service had already captured its callback and invokes it later. A second listener is rebound to the same source, and an old captured notification then arrives. How should both lifetimes be made safe, and what regression cases should be added?
