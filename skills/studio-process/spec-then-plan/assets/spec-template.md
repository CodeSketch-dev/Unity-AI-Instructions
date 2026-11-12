# <Feature> Design

**Date:** YYYY-MM-DD
**Target project:** <name>
**Reference projects / evidence:** <paths, videos with timestamps, screenshots>
**Fidelity:** exact | faithful | free (per part)

## Goal
<What the player/team gets, in observable terms. Completion means wired, compiled and played, not just scripted.>

## Constraints
- Framework/packages to use (and ones not to introduce):
- Platform/perf budget (low-end Android first):
- Reference rules (what must match, what may differ):
- Things to preserve (other agents' changes, existing saves, GUIDs):

## Decisions and assumptions
| Decision | Chosen | Alternatives considered | Why |
|---|---|---|---|

## Architecture
<Components and ownership; data records; config assets + registry/factory; events; state machines; async/cancellation; pooling. Diagram only if it clarifies.>

## Data and assets chain
<Data record -> config asset -> factory entry -> runtime consumer -> prefab/scene wiring -> editor installer/bake step.>

## Behavior details
<Rules, numbers (with source), edge cases, empty/full/locked states, failure paths, FTUE.>

## UI/UX (if any)
<Placement per `mobile-hud-layout`, states, animations, text solution, reference screenshots to compare.>

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|

## Out of scope

## Acceptance criteria (checkable)
- [ ] Compiles; Console has no new errors/warnings from this work
- [ ] <Play Mode path> works from the real entry flow
- [ ] <screenshot matches reference at 9:16, 9:20, 3:4>
- [ ] <numbers within target band, evidence: simulation/profiler>
- [ ] Save/load and fresh-save paths verified
- [ ] Provenance/licences recorded for new external assets
