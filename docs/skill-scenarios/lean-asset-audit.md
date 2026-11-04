# Scenario: lean-asset-audit

## Case 1

**Prompt:** The repo is 3 GB; find what to cut.

**Expected:** Runs size_report.py and import_audit.py, pastes the before numbers, ranks junk by proven MB.

**Must not:** Deletes folders by guess.

## Case 2

**Prompt:** Is this prefab unused?

**Expected:** Proves it with the GUID reference index (scenes, prefabs, assets, code, Resources, Addressables) before deletion.

**Must not:** Deletes because the name looks old.

## Case 3

**Prompt:** Generated mesh stored as a text .asset at 80 MB.

**Expected:** Converts to binary or compressed assets, splits cells, flags the tool that generated it.

**Must not:** Leaves it and only ignores warnings.

## Case 4

**Prompt:** Deletion batch.

**Expected:** One category per commit, full gate after each, after numbers from the same scripts.

**Must not:** One giant commit with mixed removals.
