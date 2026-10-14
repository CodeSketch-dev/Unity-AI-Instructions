# Scenario: settings-pause-offline

**Prompt:** Build the settings and pause popups.

**Expected:** Binds data to audio, sets timeScale 0 with unscaled tweens, resyncs timers on resume.

**Must not:** Pauses with scaled tweens so the popup never animates.
