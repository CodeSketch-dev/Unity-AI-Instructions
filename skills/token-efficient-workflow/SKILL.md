---
name: token-efficient-workflow
description: "Rules that cut tokens and time: read less, query indexes, batch calls, small outputs, delegate wide search, avoid rework, clean hand-off. Use at the start of long Unity/clone sessions or when slow/costly."
---

# Token- and time-efficient workflow

Most tokens in a clone session are spent on four things: re-learning the project, searching big reference projects blindly, reading huge files or logs, and redoing work because intent or fidelity was unclear. Fixing those gives the biggest savings; micro-trimming wording gives the least.

## 1. Start cheap
- Read only the project's context map (`project-context-map`) and `docs/feedback-notes.md`. Do not survey the repo to "get oriented"; the map exists so you do not have to.
- Load only the skills the current phase needs (`clone-pipeline` tells you which); each skill pulls its `references/` files on demand, not up front.

## 2. Find things with indexes, not walks
- Reference projects (the `References` table in `docs/clone-plan.md`): query the prebuilt index (`reference-index`), e.g. `query pet cage`, instead of recursive grep over thousands of files. One query is ~10 lines; one blind exploration can be thousands.
- In the current project: `Grep` with `output_mode: files_with_matches` first, then targeted `Read` with `offset/limit`. Use `Glob` for names. Never open a file whole just to find one function.
- If a wide, open-ended search is truly needed (many directories, unknown names), delegate it to a subagent and ask for a conclusion of at most ~200 words with file paths. Do not delegate a lookup you can do in one query.

## 3. Never read what a tool can summarize
| Big thing | Do this instead |
|---|---|
| Scene/prefab YAML (tens of thousands of lines) | Editor tooling (hierarchy, components, serialized values) or the index; never `Read` the YAML whole |
| Editor.log / Console dump | `unity-log-triage` script (deduplicated, compile errors first) |
| Large generated assets, meshes, meta files | Skip; check counts/GUIDs with a script |
| Long command output | Filter at the source (`| head -40`, `--limit`, `--json` plus a field filter); write detail to a file and print one summary line |
| Screenshots | Scale 0.4-0.5 unless fine detail matters; prefer text extraction when you only need text |

## 4. Batch
- Independent tool calls go in one message. Several small Editor operations go in one editor script or one batch call instead of many round trips (keep each call short and idempotent: `editor-tool-authoring`).
- Edit many scripts, then refresh/compile once, then read the Console once. Do not recompile after every edit (`unity-fast-iteration`).

## 5. Avoid rework (the biggest saver)
- Plan anything non-trivial with `spec-then-plan`; one batched clarifying question with a recommended default is cheaper than two wrong implementations.
- Fix the fidelity label and reference evidence before building (`game-clone-recon`, `reference-port`). "Looks different" iterations are the most common waste.
- Verify with `done-means-wired` once, properly, instead of repeated "is it working?" rounds.
- Do not re-read a file you just edited (the edit tool errors if it failed), and do not re-derive facts already established in the conversation or the notes.

## 6. Keep your own output small
- Final reports: what changed, what was verified, what was not, what is next, in ~10-15 lines. Tables for lists, no narration of every tool call, no restating the request.
- Do not paste whole files or logs into the chat; point to the path and line.

## 7. Context hygiene across long sessions
- Write durable state to files as it happens (`feedback-notes-sync`, the context map's "current state"), then it is safe to compact or start a fresh session at a task boundary; the new session reads the two short files instead of replaying history.
- One major task per session where possible; unrelated tasks go to a new session.
- Keep stable instructions stable: avoid editing the global instruction files mid-session (it invalidates caching) and keep them short; push detail into skills.

## 8. Route work to the right effort
- Mechanical tasks (renames, asset transfer runs, formatting, bulk wiring from a plan) can run on a lighter model/effort or a subagent; reserve the strongest model and deepest thinking for design, debugging root causes and balance.
- Parallelize only truly independent work with disjoint files (never two writers on one scene/prefab).

## Self-check before a big step
Is there an index/map for this? Can a script summarize it? Can I batch it? Is the reference/intent unambiguous? If any answer is "no", fix that first.
