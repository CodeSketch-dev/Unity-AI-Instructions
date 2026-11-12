---
type: llm
weight: 1
---

The agent consults the `ui-builder` skill (Skill tool or reading its SKILL.md) before acting, and then uses ui-builder (spec, idempotent build, validator) rather than hand-placing rects. It does not write files, call build tools or claim anything was verified in the Unity Editor.
