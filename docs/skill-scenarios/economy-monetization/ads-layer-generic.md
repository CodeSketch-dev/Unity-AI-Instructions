# Scenario: ads-layer-generic

**Prompt:** Add a rewarded 'double coins' button to the result popup.

**Expected:** Calls AdsHelper only, handles not-ready with toast and false, logs placement by enum name, tests no-fill via the fake provider.

**Must not:** Calls the SDK directly from the popup, fires the callback twice, or hardcodes keys.
