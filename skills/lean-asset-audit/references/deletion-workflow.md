# Deletion workflow (one category per batch)

1. Clean git state for the folders touched; note the commit hash as the rollback point.
2. Run `dead_assets_proof.py` (fresh). Review `SUMMARY.md`; open a few DEAD-PROVEN rows and confirm by Unity "Find References In Scene" or a text search for the guid.
3. Editor tool (idempotent, chunked, see `editor-tool-authoring`):
   - input: `dead_proven.csv` (path column), a mode flag DRY RUN / DELETE;
   - DRY RUN logs path, size and verdict note to a report file under `docs/reports/` and deletes nothing;
   - DELETE re-checks each row (file exists, `AssetDatabase.AssetPathToGUID` equals the CSV guid, path starts with an allowed root, never under Resources/Plugins) and calls `AssetDatabase.DeleteAsset(path)`; it writes the same log with the result.
4. Re-run the proof right before DELETE; if the dead set grew or shrank, stop and read why.
5. One commit per category (for example "chore(assets): remove 72 orphan generated meshes (1.0 GB)"), body lists the proof file and the numbers.
6. After each batch: refresh, compile, open every Build Settings scene, count missing scripts and missing references on scenes and prefabs, Console empty, EditMode PASS/SKIP counts equal to the baseline, Play 5 s on the main scene.
7. Derived folders: `git rm -r --cached <folder>`, add the ignore rule, `git check-ignore -v <folder>/<file>`, commit; the files stay on disk for the tool that writes them.
8. Record before/after in the lean report; mark what was not measured (device RAM, load time).
9. If a batch breaks something, `git revert` that single commit; never mix a deletion batch with feature work so the revert is clean.
