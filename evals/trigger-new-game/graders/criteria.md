---
type: llm
weight: 1
---

The agent consults the `new-game-bootstrap` skill (Skill tool or reading its SKILL.md) before acting, and then asks before creating a Unity project, uses new-game-bootstrap, never edits ProjectSettings YAML by hand. It does not write files, call build tools or claim anything was verified in the Unity Editor.
