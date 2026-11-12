# Scenario: house-editor-tools

## Case 1

**Prompt:** Add a bake button for a new feature.

**Expected:** Idempotent static entry, progress bar in try/finally, log file, second run changes nothing (git status), added to the optimizer Bake order.

**Must not:** Uses InitializeOnLoadMethod to re-edit assets at every reload.

## Case 2

**Prompt:** Mutate prefabs in a tool.

**Expected:** LoadPrefabContents / SaveAsPrefabAsset / UnloadPrefabContents in try/finally.

**Must not:** Edits only a scene instance override.

## Case 3

**Prompt:** Project has no tests or CI.

**Expected:** Adds Tests/EditMode and PlayMode asmdefs, static-check tests, build/version method, pre-commit missing-reference check.

**Must not:** Skips the kit because it is not in the reference.

## Case 4

**Prompt:** Auto-fix tool loops.

**Expected:** Bounded to 2 attempts per target, rest left to a human.

**Must not:** Retries endlessly.
