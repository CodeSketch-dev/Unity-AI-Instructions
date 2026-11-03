---
type: llm
weight: 1
---

The agent consults the `scene-flow-loading` skill before choosing the architecture, plus `ui-always` before any UI implementation. It inspects the actual build entry and existing provider rather than adding a network. It distinguishes preactivation tasks from tasks registered by target Awake, specifies cancellable UniTask progress registration, one busy gate and explicit allowSceneActivation gating. It preserves saved ad refusal/remove-ads, treats inventory waits as bounded, and awaits the actual shown app-open close/failure callback. It requires native logical-unit slot verification and an instrumented Play timeline, and does not claim Editor/device checks or perform writes in this read-only evaluation. Hard-fail if it proposes target Awake registration as a preactivation prerequisite or uses an arbitrary timer to enter gameplay under a still-open ad.
