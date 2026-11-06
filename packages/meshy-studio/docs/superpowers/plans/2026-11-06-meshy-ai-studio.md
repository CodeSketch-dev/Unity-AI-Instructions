# Meshy AI Studio — Implementation Plan

## Active skills

`brainstorming` (scope already complete), `spec-then-plan`, `coding-discipline-karpathy`, `test-driven-development`, `studio-non-negotiables`, `done-means-wired` (adapted to desktop wiring), `test-evidence-review`.

## Rework risks

- Meshy web UI changes: avoid selectors; keep browser path manual until live-verified.
- Secret leakage: central credential and logging redaction boundaries, plus file-byte tests.
- GUI freezes: all network/browser/job work stays off the GUI thread.
- Packaging misses Playwright browser binaries: setup/build scripts explicitly install Chromium and collect required resources.

## Tasks

- [ ] Write failing core tests for database, account import/security, scheduler, job recovery, and API mapping. Verify: failures are missing modules/behavior.
- [ ] Implement core/security modules minimally. Verify: targeted tests green, then full suite.
- [ ] Write failing tests for browser profile isolation, status mapping, redaction, and job orchestration. Verify: expected behavioral failures.
- [ ] Implement web-only automation and worker layers. Verify: full suite green without network credentials; live Google flow remains a headed manual verification step.
- [ ] Build and wire PySide6 shell and all six pages. Verify: offscreen GUI smoke test plus manual launch screenshot if desktop permits.
- [ ] Add setup/run/build scripts, sample data, README, icons/resources, and PyInstaller spec. Verify: scripts parse, app import/start smoke passes.
- [ ] Run full tests, dependency audit, secret scan, package source ZIP, and inspect archive manifest. Verify: test counts, zero shipped secrets, expected files present.
- [ ] Live Meshy integration only if a valid user credential is already available through the app/keyring. Otherwise mark create/upload/download as not live-verified.

