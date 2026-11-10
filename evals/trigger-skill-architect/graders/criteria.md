---
type: llm
weight: 1
---

The agent must consult the `skill-architect` skill first, then search existing skills (INDEX or fishnet-* folders) before creating anything and prefer extending an existing skill when one overlaps. It must back up and scan dependents before editing any existing skill, never modify vendor/plugin skills, run the lint plus the trigger evaluation script and report the numbers, and state what was not verified. A reply that only writes a SKILL.md without checking duplicates or running any check fails.
