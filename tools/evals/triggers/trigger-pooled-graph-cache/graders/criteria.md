---
type: llm
weight: 1
---

# Required behavior

- Loads or applies the `profiling-evidence` skill.
- Records allocated pool capacity separately from live count, per-frame graph rebuild count, fixed-step count and matched measurement windows.
- Rejects same-count as proof of unchanged graph input; enumerates the graph's complete authoritative logical read set and keeps dirty rebuild/publication ordering.
- Requires epoch/reset, query reorder, late-carry, and same-count/different-content regressions before skipping work.
- Distinguishes true child-job work removal from relocating a wait; compares whole-frame median/P95 and relevant worker markers, retaining adverse results.
- Does not claim device FPS from Editor timings or claim these prose checks prove code or runtime correctness.
