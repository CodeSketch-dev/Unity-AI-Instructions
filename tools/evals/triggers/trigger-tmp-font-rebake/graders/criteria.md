---
type: llm
weight: 1
---

The agent consults the `ui-text-tmp` skill before proposing font changes; compares all original TMP SDF FaceInfo fields with the newly generated asset; rescales only dimensionful metrics to the generated sampling point size; preserves atlas/glyph sampling and padding; and verifies wrapped line baselines against the original in a Play capture. It does not reuse metrics from another font.
