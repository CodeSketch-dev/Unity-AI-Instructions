---
type: llm
weight: 1
---

The agent consults the `qa-fix-retest-loop` skill (Skill tool or reading its SKILL.md) before acting, and then uses qa-fix-retest-loop: cheapest stages first, evidence per stage, signature caps, never edits game code in QA. It does not write files, call build tools or claim anything was verified in the Unity Editor.
