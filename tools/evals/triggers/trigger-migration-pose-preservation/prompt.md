---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

A backend migration removed a legacy collector component, but a coin spawn point still reads its old metadata array and quietly chooses Y=0 when the array is empty. A chunk split preserves local position but drops local rotation, and export rewrites its world orientation. What migration checks should prevent these regressions?
