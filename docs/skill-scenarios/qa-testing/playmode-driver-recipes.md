# Scenario: playmode-driver-recipes

**Prompt:** Screenshot the shop popup at three aspect ratios and tap Buy.

**Expected:** Claims blocking popups with a real tap first, ScreenCapture read next call, EventSystem raycast tap, save backed up and restored, no Clone objects saved.

**Must not:** Uses onClick.Invoke only, commits ProjectSettings runInBackground, saves scene in Play Mode.
