# Static receiver cross-reference evidence

> **For agentic workers:** extend the existing reference-dissection skill; do not infer an owner from matching field layout alone.

**Goal:** Provide a safe evidence path for identifying a static receiver when a native dump lacks a type-usage index.

**Approach:** Require exact PC-relative global/GOT slot correspondence to an independently identified typed accessor or initializer, validate address arithmetic and field offsets, and preserve unknown when the link is not exact. Add a skill-spec regression and one trigger evaluation.

**Tech Stack:** Existing Markdown skill, JSON skill spec and trigger-eval format.

**Review Focus:** slot address arithmetic; independent identity of the typed accessor/initializer; pointer-slot identity versus coincidental layout; unknown result if no exact link.

Ruling: foundation = **no**. This is a narrow reverse-reference technique, so keep it within `reference-project-dissection`; no always-on rule or hook.

## Skill scenarios

- Native type-usage index absent; expected skill loads, trace a PC-relative slot to an independently mapped typed accessor/initializer, verify address arithmetic, report owner only if exact.
- Candidate structs share offsets; expected skill rejects layout similarity as identity proof and preserves unknown without exact slot correspondence.
- Ordinary managed C# static property with no native/reference analysis; expected skill does not fire.

## Steps

- [ ] Extend the existing spec and add a trigger-eval prompt/grader first; verify RED against current guidance.
- [ ] Add the concise cross-reference method under native receiver ownership.
- [ ] Re-run skill score/lint and repo lint/tests.
- [ ] Publish from this isolated clone and verify the remote SHA.
