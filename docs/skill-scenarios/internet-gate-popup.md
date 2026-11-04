# Scenario: internet-gate-popup

## Case 1

**Prompt:** Add a no-internet popup.

**Expected:** Checks the installed framework Internet module first, uses it or a thin custom gate with adapter check plus ping and fallback URL, 5 s timeout, Try Again shows Reconnecting for at least 5 s.

**Must not:** Builds a second popup while a vendor SDK popup is still enabled.

## Case 2

**Prompt:** Rewarded ad button with no network.

**Expected:** Requests a check first, shows a localized toast and callback(false).

**Must not:** Silently does nothing or grants the reward.

## Case 3

**Prompt:** VIP / ads-removed player offline.

**Expected:** Gate bypassed when adsRemoved or vip, or when the remote flag is off.

**Must not:** Blocks a paying player.

## Case 4

**Prompt:** Verify.

**Expected:** Turns the network off, sees the popup, restores the network, popup closes on Try Again.

**Must not:** Claims done from code reading.
