# Scenario: device-tier-policy

**Prompt:** The game crashes on a low-end Android after I switch quality at runtime.

**Expected:** Explains never assigning QualitySettings.renderPipeline at runtime; edits the active URP asset per tier; adds kill switches.

**Must not:** Swap pipeline assets at runtime.
