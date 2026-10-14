# Scenario: boot-sequence-setup

**Prompt:** On a CodeSketch project the save loads late and hitches on first shop open.

**Expected:** Adds DataBlockPreloader called from the splash hook (v1) or notes automatic warmup (v2); settings->audio binding in an AfterSceneLoad hook.

**Must not:** Touch DataBlocks inside BeforeSplashScreen without noting the load cost.
