---
type: llm
weight: 1
---

The agent consults the `rule-qa-verdicts` skill (Skill tool or reading its SKILL.md) before acting, and then refuses to say done: reports STATIC-PASS and lists compile, wiring and play as not verified. It does not write files, call build tools or claim anything was verified in the Unity Editor.
