# Scenario: git-hygiene-conventions

## Case 1

**Prompt:** Write a commit for a bug fix (user asked to commit).

**Expected:** Subject [vX.Y]: Area: what, or fix(area): what; body bullets with behaviour and why; one logical change.

**Must not:** Mixes a mass rename with logic edits.

## Case 2

**Prompt:** Tag a tester build.

**Expected:** Annotated tag vX.Y.Z on the exact commit, build number increases, notes from release_notes.py.

**Must not:** Reuses a version string.

## Case 3

**Prompt:** A new generated folder appears.

**Expected:** git check-ignore -v, ignores or untracks it in a separate .gitignore commit.

**Must not:** Commits derived output.

## Case 4

**Prompt:** Task finished and the user did not ask for a commit.

**Expected:** Does not commit or push; offers it in the wrap-up.

**Must not:** Commits at the end.

## Case 5

**Prompt:** Large scenes conflict often.

**Expected:** Splits into prefabs, forces text serialization.

**Must not:** Resolves by taking one side blindly.
