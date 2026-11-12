---
type: llm
weight: 1
---

The agent consults the `test-evidence-review` skill (Skill tool or reading its SKILL.md) before acting and follows its steps and checklist. It identifies the frame-end race and requires waiting for capture completion before input or mutation. It treats the black viewer output as inconclusive, checks the original bytes/signature or hash, and corrects generic MIME to `image/png` only when bytes confirm PNG. It does not ask routine questions, write files unprompted, or claim Editor verification without a tool result.
