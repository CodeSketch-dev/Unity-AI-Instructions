# UI Layout Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Unity UI fail validation when TMP content or controls escape padded parent bounds or overlap, while giving skills a containment-first construction contract.

**Architecture:** Update the UI generation skills with one shared containment/Auto Size decision path. Extend the static YAML validator for deterministic failures and its Editor template for post-layout evidence; focused Python tests pin each detectable rule.

**Tech Stack:** Markdown skills, Python stdlib/unittest, Unity TextMeshPro and Editor validation template.

**Spec:** `docs/superpowers/specs/2026-10-16-ui-layout-contract-design.md`

## Global Constraints

- Preserve reference-driven intentional decorative Board/Frame layers.
- Do not silently truncate or rewrite visible text.
- A label that cannot fit at minimum Auto Size and safe maximum button size is a hard failure requiring design input.
- Do not edit target Unity projects from this instruction repository.
- Preserve unrelated dirty work; no reset, clean, commit or push.

## Review Focus

- Decorative frame/image layers must not be misclassified as illegal content overlap.
- TMP Overflow without Auto Size must not bypass a containment failure.
- LayoutGroup/ContentSizeFitter results must be validated in the Editor, not treated as proven by YAML.
- Parent padding must be applied before determining whether a button may expand.
- Long localized text at the configured minimum font must fail explicitly rather than clipping or covering siblings.

---

### Task 1: Generation contract in reusable UI skills

**Files:**
- Modify: `skills/ui-text-tmp/SKILL.md`
- Modify: `skills/ui-icon-label-layout/SKILL.md`
- Modify: `skills/ui-button-anatomy/SKILL.md`
- Modify: `skills/ui-validator/SKILL.md`

**Produces:** A shared written contract for padded parent content areas, safe preferred-size expansion, TMP Auto Size, centered icon+label groups and fail-on-unfit behavior.

- [x] Add the containment-first hierarchy and TMP sizing requirements to the four skill entrypoints without duplicating unrelated guidance.
- [x] Document decorative-layer exemptions and the required stop condition for text that cannot fit safely.
- [x] Run strict skill lint and verify the new rules are discoverable from each relevant skill.

### Task 2: Static UI validator hard failures

**Files:**
- Modify: `skills/ui-validator/scripts/ui_validator.py`
- Modify: `tools/tests/test_ui_validator_ext.py`
- Modify: `tools/tests/test_ui_validator_rules2.py`

**Produces:** Static rules that return `FAIL` for detectable TMP overflow/escape from a padded content container and for content sibling intersection, without rejecting exempt background/frame layers.

- [x] Write failing tests for long text at minimum Auto Size, parent-content escape, valid padded content and decorative frame exemption.
- [x] Implement parsed padding/container metadata and the named `UI-TEXT-FIT` / `UI-CONTENT-CONTAINMENT` findings with precise paths.
- [x] Run the focused validator test modules and confirm the new violations exit non-zero from the CLI.

### Task 3: Runtime layout-rebuild evidence

**Files:**
- Modify: `skills/ui-validator/assets/Qa_UiValidator.cs.txt`
- Modify: `skills/ui-validator/SKILL.md`
- Modify: `tools/tests/test_ui_validator_cli2.py`

**Produces:** An Editor-side template that forces layout rebuilds, reads TMP preferred/resolved bounds and reports the same hard rule names across target aspect ratios.

- [x] Extend the template's JSON schema with `UI-TEXT-FIT` and `UI-CONTENT-CONTAINMENT` evidence.
- [x] Document compilation/run expectations and the requirement to treat a missing runtime pass as unverified.
- [x] Run focused tests, strict skill lint, then the full UI-validator test group.
