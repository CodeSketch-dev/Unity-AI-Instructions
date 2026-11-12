# Scenario: rating-prompt-flow

## Case 1

**Prompt:** Add a rate-us prompt after a level win.

**Expected:** Eligibility: not rated, not asked this session (non-persisted), tutorial done, cooldown and launch counter; asks at the win moment.

**Must not:** Asks on first launch or on every win.

## Case 2

**Prompt:** Player picks 1-2 stars.

**Expected:** Bad path: feedback or dismiss without opening the store review; no repeat in this session.

**Must not:** Sends low raters to the store.

## Case 3

**Prompt:** In-app review dialog does not appear (quota).

**Expected:** Falls back to opening the store page; persists the ask counter so there is no retry loop.

**Must not:** Retries every session forever.

## Case 4

**Prompt:** Offline player and iOS.

**Expected:** Handles offline safely and implements both Android and iOS branches.

**Must not:** Leaves the iOS branch commented out.
