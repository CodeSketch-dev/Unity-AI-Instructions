# Scheduled dead-asset sweep

Cadence: every ~2 weeks and before each release tag (the reference history shows sweeps on that rhythm; one skipped period later cost a 270k-line purge).

Steps (owner approves deletions; the sweep itself is read-only)
1. `lean-asset-audit/scripts/dead_assets_proof.py` with the project's candidate folders, `--scenes --duplicates --packages --derived <folders>`; output to a dated folder under the reports directory.
2. Diff `dead_proven.csv` against the previous sweep: new rows are the work list.
3. Dry-run Editor delete tool (`lean-asset-audit/references/deletion-workflow.md`), review the log.
4. Delete one category per commit: `chore(assets): remove <n> unreferenced <category> (<MB>)`, body has the proof file path.
5. Verify (compile, open every build scene, missing-reference check, Console, EditMode counts) and record the lean metrics table.
6. Whole-feature removal (a dropped minigame, a retired popup) is its own commit with code + prefabs + assets + tests together.

Automation idea: schedule the read-only proof run (scheduled task or CI cron) and attach `SUMMARY.md` to the report; never schedule the delete step.
Also per release: churn report (`scripts/churn_report.py`), count of low-information commit subjects, number of binary-serialized scenes, largest asset, git pack size.
