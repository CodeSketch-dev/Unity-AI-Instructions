# Rollback rules

1. Before every batch: note the commit hash (or create a lightweight tag/stash) and keep the working tree otherwise clean for the touched paths.
2. If a batch is committed and a later gate fails: `git revert <batch commit>` (history stays honest). One batch = one commit makes this a one-liner.
3. If the batch is not committed: restore only the paths you changed (`git restore -- <paths>`), never the whole tree; other agents or the owner may have edits in flight.
4. For a risky bulk run (mass renames, deletions) first stash recoverably: `git stash push -u -m "<why>" -- <paths>`. Ignored files are NOT stashed; generated assets may need regeneration.
5. Never use `git reset --hard`, `git clean -fd`, force push or history rewrite without explicit owner approval. A git history rewrite to shrink the pack is a separate owner decision.
6. After any rollback: refresh, compile, reopen scenes, re-run the gate that failed, record the failure and the cause in the batch summary.
7. A deleted asset that turns out to be needed: restore it from git by path, then add its reference to the proof tool's keep-list (string load, Addressables, folder reference) and re-run the proof.
8. Binary serialized files (binary scenes, binary assets) cannot be merged: coordinate a single writer and convert to text serialization in its own batch.
9. Keep the Editor and the disk consistent: after external file changes reload scenes/prefabs from disk before saving, otherwise the Editor writes its stale copy over the rollback.
