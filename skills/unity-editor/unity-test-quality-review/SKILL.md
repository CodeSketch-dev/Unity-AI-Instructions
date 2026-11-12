---
name: unity-test-quality-review
description: "Use when writing or reviewing Unity EditMode/PlayMode tests: checklist for tests that can fail, assert on the unit not mocks, stay isolated, and cover five categories per system."
triggers: test review, review tests, test quality, editmode, playmode, assert, mock, test checklist, kiem tra test, test dung chua, test yeu
---

# Unity test quality review

Merges a friend's `reviewing-tests` and `unity-testing` skills (FakeMG/ai-instructions) into our flow. It complements `senior-tester`, `qa-editmode-validators` and `superpowers:test-driven-development` (which require watching a test fail first).

## Eight-question checklist (any "no" is a finding)
1. Could this test fail? It must break if the behaviour breaks (see the TDD red step).
2. Does it assert on the unit under test, not on a mock?
3. Does it use only public behaviour? A design you cannot test through public API is flagged for redesign, never tested via reflection.
4. Is it isolated and order independent (state reset in TearDown, no shared statics)?
5. Are external systems (audio, persistence, time, ads, network) replaced by test doubles, with the calls asserted?
6. Is the test body trivial (no loops/ifs deciding the outcome)?
7. Is it in the right place with clear naming and Arrange/Act/Assert layout? One behaviour per test.
8. Is every behaviour and category covered?

## Five categories per system
Happy path, edge cases, failure cases (assert the specific exception or the clamped result), integration points, regression guards.

## EditMode vs PlayMode
- EditMode: pure logic, no frame loop, physics or MonoBehaviour lifecycle. A MonoBehaviour tested in EditMode is a finding.
- PlayMode: needs the game loop, scenes or physics. Build objects from prefabs/factories the way the game does, not bare `new` on components; dispose everything in teardown so nothing leaks into the next test.
- Prefer code-built objects; use prefab assets in tests only when serialization, lifecycle or hierarchy is what is under test.

## Output of a review
Title `Test Review: <name>`, findings grouped Critical / Significant / Minor with file:line and the failing question number. Missing coverage is a finding. Review only; do not edit in the same pass.

## Project note
Mocking and DI libraries differ per project (the source repo uses NSubstitute and VContainer); use what the project already has, and never add one just for a test.
