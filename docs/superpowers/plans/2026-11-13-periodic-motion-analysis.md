# Periodic-motion video analysis guard

> **For agentic workers:** update the existing gameplay-video analysis skill only; preserve evidence labels and do not infer runtime speed from ambiguous silhouettes.

**Goal:** Prevent coarse sampling from causing repetitive or symmetric motion to be mislabeled static.

**Approach:** Add one compact aliasing check to `gameplay-video-analysis`, with a skill spec and one trigger evaluation. Require inspection of the original clip plus dense samples at multiple non-commensurate offsets over repeated cycles.

**Tech Stack:** Markdown skill, JSON skill spec, existing trigger evaluation format.

**Review Focus:** coarse-sample aliasing; repeated symmetric poses; enough time span to see a cycle; no inferred speed/direction without measured temporal evidence.

Ruling: foundation = **no**. This is a video-analysis technique; keep it within the existing routed skill, with no always-on rule or prompt hook.

## Steps

- [ ] Add the spec and trigger evaluation first; confirm baseline skill score fails the aliasing requirements.
- [ ] Add the smallest warning/checklist to the existing skill.
- [ ] Re-run skill score and lint; run repo lint/tests.
- [ ] Publish from the isolated clone and verify the remote commit SHA.
