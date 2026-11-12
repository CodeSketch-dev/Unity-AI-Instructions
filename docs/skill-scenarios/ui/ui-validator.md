# Scenario: ui-validator

**Prompt:** Validate the new HUD prefab and the popup structure.

**Expected:** Runs ui_validator.py with --kind and --hud and --project, fixes FAILs, records reasoned exceptions only where the reference differs, runs ui_contrast on the screenshot.

**Must not:** Treat WARN-level heuristics as proof or silence rules without reasons.
