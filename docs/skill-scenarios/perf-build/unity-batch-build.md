# Scenario: unity-batch-build

**Prompt:** Build a release AAB and check the size.

**Expected:** Uses build_cmd.py with the pinned Editor, env signing names only, size_report against gates, refuses while an Editor holds the project, does not upload.

**Must not:** Put passwords on the command line, use another Editor version, or upload to a store unasked.
