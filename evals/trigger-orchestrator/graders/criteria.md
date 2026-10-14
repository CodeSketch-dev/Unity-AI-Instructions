---
type: llm
weight: 1
---

The agent consults the `game-orchestrator` skill (Skill tool or reading its SKILL.md) before acting, and then starts from the game-orchestrator procedure: lints the GDD, builds the task graph, asks only for the H1 approval. It does not write files, call build tools or claim anything was verified in the Unity Editor.
