---
type: llm
weight: 1
---

The agent consults the `mobile-input-controls` skill before recommending a change; distinguishes discrete actions from continuous holds; preserves touch/finger identity and UI-vs-world exclusion for the edge; requires a coalesced down+up in one input update to dispatch exactly once and a no-input following update to dispatch zero times; and keeps real-device gesture evidence distinct from synthetic tests. It must not replace held behavior with edge-only input or claim a device fix without a rebuilt-player gesture result.
