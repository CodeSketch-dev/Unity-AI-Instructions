# <Feature> Implementation Plan

**Goal:** <one sentence>

**Architecture:** <2-3 sentences: who owns what>

**Tech stack:** <Unity version, framework packages, MCP server>

**Spec:** `docs/specs/YYYY-MM-DD-<topic>-design.md`

## Global constraints
- <framework rules, namespace/naming, preserve GUIDs, source prefab not scene override, no commits unless asked, preserve others' changes>

## Review focus
- <the likeliest failures for this feature and which task tests them>

---

### Task 1: <name>

**Files:**
- Create: `<exact path>`
- Modify: `<exact path>` (what part)
- Test: `<exact path>`

**Interfaces:**
- Consumes: <types/assets/events from earlier tasks or existing code>
- Produces: <types/assets/events later tasks rely on>

- [ ] **Step 1: <write the failing test / write the inspection check>**
  Expected: <what fails and why>
- [ ] **Step 2: <implement>**
- [ ] **Step 3: <verify>**
  How: <MCP call / Play path / screenshot / test runner>. Expected: <observable result>
- [ ] **Step 4: <record>** (notes, provenance, plan checkbox)

### Task N: Integration and wiring
- [ ] Wire into the source prefabs/scenes, create config assets, register in factory, run editor installer/bake
- [ ] Save scene/prefabs, refresh, compile, read Console
- [ ] Play from the real entry flow; exercise main paths and edge cases
- [ ] Screenshot comparison with the reference (if visual)
- [ ] Report: verified vs not verified; update feedback notes

## Self-review checklist
- Every acceptance criterion in the spec maps to a task
- No placeholders ("TBD", "handle edge cases") remain
- Names, signatures and paths are consistent across tasks
- Risky operations (mass instantiate, generators, deletes) have guards and are chunked
