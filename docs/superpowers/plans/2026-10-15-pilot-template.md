# Local Unity Pilot Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portable Unity 6 template and generate the Sky Climb pilot from its bundled GDD.

**Architecture:** The template lives under `skills/new-game-bootstrap/assets/game-template-unity`; a stdlib copier creates a local pilot without a remote. Existing bootstrap, preflight, GDD and QA tools validate the result without editing any reference project.

**Tech Stack:** Unity text assets, C#, JSON, Python stdlib, unittest.

**Spec:** `docs/superpowers/specs/2026-10-15-pilot-template-design.md`

## Global Constraints

- Do not edit a reference Unity project or use remote/cloud/publishing flows.
- Use no packages beyond pinned Unity registry package versions.
- Do not claim Unity compilation or runtime evidence until a compatible local Unity invocation succeeds.
- Preserve existing dirty suite work; no reset, clean, commit or push.

## Review Focus

- Destination is non-empty or inside a reference project: copier must refuse.
- Template package lock and manifest drift: preflight must stay green.
- Tokens remain after bootstrap: preflight must fail.
- Pilot has no Unity executable: report static-only evidence, never a compile claim.
- GDD graph references a missing skill: generation must reveal it before work begins.

---

### Task 1: Portable template and copier

**Files:**
- Create: `skills/new-game-bootstrap/assets/game-template-unity/**`
- Create: `skills/new-game-bootstrap/scripts/create_pilot.py`
- Modify: `tools/tests/test_release_scripts.py`

**Produces:** `create_pilot.py --source SOURCE --destination DEST [--dry-run] -> int` which refuses an existing non-empty destination and copies template files without generated folders.

- [ ] Write failing tests for dry-run, empty destination creation and non-empty destination refusal.
- [ ] Run the focused tests and observe the missing copier failure.
- [ ] Add the text-only Unity 6 template and minimal copier.
- [ ] Run focused tests green.

### Task 2: Sky Climb pilot flow

**Files:**
- Create: `_pilots/sky-climb/**` (ignored throwaway project)
- Modify: `.gitignore`, `tools/tests/test_release_scripts.py`, `docs/agent-handoff.md`

**Consumes:** Task 1 copier; existing Sky Climb GDD and bootstrap/preflight/GDD tools.

- [ ] Write a failing integration test that copies the template, writes a valid config, runs bootstrap/preflight/GDD lint/task graph and asserts no missing skill.
- [ ] Run it to observe the missing integration path.
- [ ] Implement the integration helper and generate the real pilot.
- [ ] Run focused test and static QA on the pilot.

### Task 3: Unity availability and handoff

**Files:**
- Modify: `docs/agent-handoff.md`, `docs/RESUME-NEXT.md`, `docs/superpowers/plans/2026-10-15-ai-game-pipeline.md`

**Consumes:** generated pilot and validation outputs.

- [ ] Detect compatible Unity executable without launching or changing the pilot.
- [ ] If available, run local batch compile only after confirming no Editor lock; otherwise record static-only limitation.
- [ ] Re-run the full suite and strict lint, then record measured pilot outcomes and next action.
