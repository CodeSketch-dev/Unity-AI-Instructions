---
name: multi-agent-coexistence
description: Protocol so Claude, Codex, subagents, the human and the Editor do not overwrite each other (re-read before edit, snapshot/check/claim via workspace_guard.py). Use at session start in shared repos and when files change unexpectedly.
---

# Multi-agent coexistence

The failure: agent A reads a file, spends minutes working; agent B changes the file; A writes from its old copy and B's change is gone. A's *memory* of the file is the bug. **The disk is the source of truth, and your change must be applied on top of what is on disk now.** Same hazard with the Unity Editor holding an old scene in memory.

## The protocol: read, snapshot, edit, check, write, re-snapshot
1. **Session start**: `python -I scripts/workspace_guard.py status` (claims and git-dirty files), `git status --short` and `git log -5 --oneline`, read the tail of `docs/agent-handoff.md` and `docs/feedback-notes.md`. Dirty files you did not create are probably the other agent's work in progress.
2. **Read fresh** the file you are about to change. Treat anything you read earlier as stale after: a compile or domain reload, a Play Mode run, a long MCP/tool call, a subagent finishing, a context compaction, another agent's reported activity, or more than a few minutes.
3. **Snapshot** what you read: `workspace_guard.py snapshot --agent <claude|codex> <paths>`.
4. **Edit minimally** with a targeted patch/Edit that carries surrounding context. Never rewrite an existing file from memory and never `Write` over a file you have not read in this step. Do not reformat unrelated lines.
5. **Check right before writing/saving**: `workspace_guard.py check --agent <name>` (exit 1 = someone changed a file since your snapshot). Also treat a tool error such as "file modified since read" or a failed patch as the same signal.
6. **If changed**: re-read the file, merge your intent into the *current* content (their edit stays, yours goes on top), snapshot again, then write.
7. **After your own write**: snapshot again so your change is not later reported as foreign.
8. **Handoff** when a task touched shared areas: append one line to `docs/agent-handoff.md`: `YYYY-MM-DD HH:MM <agent> | files | what changed | what the other side must re-read or reload`. Then release claims.

The script (`workspace_guard.py`, Python 3, no dependencies) keeps its state inside `.git/agent-guard/`, never under `Assets/`; run `python -I scripts/workspace_guard.py --help` for details. It is an aid, not a lock manager: the discipline is the point, so apply steps 2-6 even when the script is not available (compare `git diff`/hash or simply re-read).

## CodeGraph is not coordination
CodeGraph can accelerate source exploration when a `.codegraph/` index exists, but its SQLite index and file watcher are derived state. It is not a lock, conflict detector, or authority over the current disk/Unity Editor state. After concurrent code edits, allow/check the index update before using a result; still re-read the target file, run the workspace guard (or compare hashes when the guard cannot write its state), and claim shared Unity assets before mutation.

## Never do
- Restore or "clean up" other people's changes: no `git checkout --`, `restore`, `reset`, `stash`, `clean`, no copying an older version or backup over a newer file.
- Bulk formatting, repo-wide renames, or regenerating generated output while the other agent may be editing its source.
- "Fix" a compile error or odd diff in a file you did not touch before checking that it is not the other agent's half-finished edit: wait, ask, or report it (`unity-log-triage` shows which file/line).
- Continue silently after discovering your copy was stale: merge, then tell the user in one line what changed and how you merged.

## When intents conflict
If both versions change the same lines in incompatible ways, stop. Show the user both versions (short quotes) and ask which wins. Do not pick silently.

## Unity-specific hazards
- **Editor memory vs disk**: the Editor may hold an older copy of a scene/prefab than the file on disk and overwrite the disk file on save. If `check` shows an open scene/prefab changed on disk, reload it from disk (reopen the scene or refresh the AssetDatabase) before any save through MCP.
- **One writer per scene/prefab**: claim it (`workspace_guard.py claim --agent <name> <path> --note "..."`), prefer editing through Editor tooling, save promptly, release. If a claim is held by the other agent, do other work or ask; do not edit text YAML under an open Editor session.
- **Generators/builders** (e.g. a HUD builder): claim the builder and its output together; re-run only after `check`; the output belongs to the builder (`editor-tool-authoring`).
- **Scripts**: Unity recompiles on disk changes, so both agents see each other's half-done edits as errors. Do not patch over them.
- **Meta files, GUIDs, library**: never regenerate, delete or reformat.
- **Shared Editor state**: check Editor state before editing (not in Play Mode; edits made in Play Mode are lost); expect the other agent's QA to start/stop Play Mode or change `timeScale`; avoid long generator runs while someone is testing; keep MCP calls short (`unity-mcp-workflow`).
- **Subagents** you spawn count as another writer: give them disjoint files and never let two write the same scene/prefab.

## Shared documents
Feedback notes, plans with checkboxes, project map and handoff are append/edit-your-lines files. Re-read the tail immediately before appending, change only your own lines, preserve line endings and BOM, never rewrite the whole file.

## Commits
No commits/pushes unless asked; the human integrates. If the working tree is dirty with someone else's work, never commit "everything".
