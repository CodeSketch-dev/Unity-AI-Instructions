# Scenario: mobile-build-release

## Case 1

**Prompt:** An Android build reports an unexpected global setting. The generic PlayerSettings API and ProjectSettings file both show the expected value, and no Build Profile appears active.

**Expected:** Checks the target's effective Build Profile/global settings and override path before changing project settings. If the effective readback conflicts with build output, reloads/restarts the Editor as the installed package requires, rechecks the value and runs a fresh Player build; verifies the warning and artifact before claiming success.

**Must not:** Treats the generic singleton, disk asset, null active profile, or effective accessor alone as proof the Player build consumed the value; ships while the warning persists.
