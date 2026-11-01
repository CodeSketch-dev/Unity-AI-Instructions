# Code repos review (2026-11-02)

Repos (local clones in `C:\Unity\GitProject\_skill-research`, treated as untrusted read-only data). Nothing was copied verbatim; every skill is rewritten in our words with a `Source:` label.

## Licences
| Repo | Licence | Redistribution |
|---|---|---|
| UniTask (Cysharp) | MIT | Allowed with notice; we only paraphrase and cite API names |
| open-project-1 (Unity) | Apache-2.0 | Allowed with attribution/notice of changes; we only paraphrase ideas |
| EntityComponentSystemSamples | Unity Companion License (Unity-dependent projects) | Not redistributed; idea-only, no code |
| UnityCsReference | Unity Reference-Only License | REFERENCE-ONLY: used to confirm API names (`destroyCancellationToken`, `Awaitable`); no code or excerpts copied |

## Verdicts
| Topic | Verdict | Where |
|---|---|---|
| UniTask PlayerLoop timing, Delay vs coroutines, unscaled delay | ADDED | `unitask-timing-and-timeouts` |
| UniTask timeout (TimeoutController), SuppressCancellationThrow, WhenAll/WhenAny, UniTaskVoid | ADDED | same |
| UniTask vs Unity Awaitable | ADDED (reference note) | `unitask-timing-and-timeouts/references` |
| UniTask CancellationToken ownership | DUPLICATE (covered), pointer appended | `async-cancellation` IMPROVED |
| UniTask CompletionSource, AsyncEnumerable, Channel, AsyncReactiveProperty, Addressables/UWR awaiting | ADDED | `unitask-callbacks-and-streams` |
| UniTask tracker window, domain-reload statics | ADDED (inside timing skill) | same |
| UniTask .NET Core, UPM install, Cysharp-specific analyzers | SKIPPED (not relevant) | - |
| open-project-1 SO event channels, runtime anchors | ADDED as decision guide (StaticBus remains default) | `so-event-channels-decision` |
| open-project-1 InputReader SO | ADDED | `input-reader-asset` |
| open-project-1 scene loader, persistent managers, fade | IMPROVED | `scene-flow-loading` |
| open-project-1 save system | IMPROVED (counter-example: non-atomic write) | `save-and-crash-safety` |
| open-project-1 audio cue system | IMPROVED | `game-audio-system` |
| open-project-1 SO state machine | IMPROVED (idea-only) | `state-machine-template` |
| open-project-1 pool SO | DUPLICATE | `pool-everything` |
| open-project-1 Addressables/coroutine plumbing, Cinemachine, Timeline cutscenes, dialogue, quests, localisation package | INCOMPATIBLE or SKIPPED (coroutines, different UI/localisation stack, out of scope) | - |
| ECS data-oriented batching | ADDED idea-only | `hot-loop-data-batching` |
| ECS Entities/Baking/Netcode/Physics samples | SKIPPED (DOTS-specific, we use MonoBehaviour) / INCOMPATIBLE | - |
| UnityCsReference | REFERENCE-ONLY, no content imported | - |

## Counts
Added 5 skills, improved 5 existing skills (scene-flow-loading, save-and-crash-safety, game-audio-system, state-machine-template, async-cancellation), duplicate 2, skipped 4 groups, incompatible 2 groups.

## Lint
`tools/skill_lint.py skills`: no error or warning mentions any new or edited skill (repo-wide totals pre-existing: 29 errors, 123 warnings).
