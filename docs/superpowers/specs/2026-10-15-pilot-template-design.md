# Local Unity pilot template design

Status: approved by the user for autonomous implementation on 2026-10-15.

## Intent

The suite must turn a lint-clean Roblox-style GDD into an actual local Unity project, rather than stopping at plans and templates. The first pilot is Sky Climb, a bundled low-risk obby GDD. It proves the handoff from suite tooling to a fresh project without changing a reference project or using protected assets.

## Goals

- Ship a portable `game-template-unity` source tree inside `new-game-bootstrap`.
- Produce a fresh Sky Climb pilot from that source tree with `new_game.py` and a valid `project.config.json`.
- Make the template pass repository preflight and static QA before Unity is invoked.
- Keep Unity-only work explicitly unverified when no compatible local Unity executable or MCP connection is available.

## Non-goals

- No reference-project edits, packages copied from references, cloud builds, publishing, SDK keys, signing, or paid evals.
- No claim of gameplay, scene, compile, or device success without actual Unity evidence.

## Design

The template is an installable skill asset, not a separate remote repository. It contains only portable text/source files: ProjectVersion, manifest/lock, ignore files, project config with tokens, first-party folders, runtime/editor asmdefs, null services, build templates, gate JSON, and documentation stubs. A small `create_pilot.py` tool copies the template to a user-selected empty destination and initializes a local git repository; `new_game.py` then performs its existing token replacement and stubs. The pilot GDD remains in the suite and task-graph output is saved inside the pilot.

## Constraints

- Unity 6 target; only registry packages in the template, no unpinned git dependency.
- First-party namespace is `Game`; product-specific values come only from config replacement.
- All files/docs/comments are English; chat is Vietnamese.
- Pilot path is under the suite workspace and is ignored from the suite repository.
- Tests use Python stdlib and run outside the filesystem sandbox when they need Windows Temp.

## Acceptance evidence

1. `create_pilot.py --dry-run` reports the exact copy target and changes nothing.
2. A real generated pilot passes `new_game.py --dry-run`, then `new_game.py`, `project_preflight.py`, GDD lint and task graph generation.
3. Static QA finds no hard issue in the template-owned first-party files.
4. Unity batch/MCP outcome is recorded as verified only if an actual compatible local Unity run succeeds.
