---
type: llm
weight: 1
---

The agent consults the `reference-project-dissection` skill; derives the PC-relative global/GOT slot address and cross-checks that exact slot against an independently identified typed accessor or static initializer; verifies address arithmetic and relevant field offsets; distinguishes pointer-slot identity from coincidental matching layout; and reports ownership unknown when no exact link is found. It must not guess from shared offsets alone.
