# Pattern: rating

Source: report 07 sec 4 row 5 (`RatingPopup`; sizes VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Timing logic: `recipe-retention-timers`.

## Behavior
- `RatingHelper.CanShow()` decides (after a win/level-up moment, not on first session, cool-down between asks, never twice after a "Good"). The `Block` image is a full-stretch input blocker with a dim.
- Good -> native store review prompt, sets `RatingDone` and `RatingInThisSession`; Bad -> dismiss (optionally a feedback link), sets the in-session flag only.
- Show at a happy moment only; never interrupt gameplay or an ad.

## Binding
`Data_Rating` (done, last ask UTC, ask count, in-session flag), analytics `rating_ask` / `rating_result`.

## Variants
1. Bad path: dismiss (default) / feedback form link. 2. Trigger: after N levels (default) / after a big reward.

## Checks
Never shows twice in a session; store prompt called only on Good; Back key dismisses like Bad; contract lints.
