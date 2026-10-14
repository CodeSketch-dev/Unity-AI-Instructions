# Pattern: revive-result

Source: report 07 sec 4 row 6 (`Result_Revive_Checkpoint` and variants; sizes VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Ad flow: `ads-popup-flow`.

## Regions
Scale 748x725 > Board 665x512; title, description (525x50), countdown ring 147 (fill 174) in the centre, one revive button 275x105 (`Btn_Revive` rewarded ad or `Btn_Revive_Free`, same slot), `Btn_NoThanks` 275x85 hanging below the board.

## Behavior
- Countdown fills (default 5 s); on expiry or No-thanks the death/result flow continues. No-thanks appears after open + 0.5 s (scale 0 -> 1, 0.25 s) so it is not mis-tapped (`ui-popup-anatomy`).
- Revive grants the revive only after the ad completes (or the free revive is consumed); restores the checkpoint state; pauses the countdown while the ad plays.
- Variants of the same popup: Killed (death cause), Stage (stage clear), Skip (skip stage by ad).

## Binding
Revive count/limits per run, ad service, checkpoint data, analytics (`revive_shown`, `revive_accepted`).

## Variants
1. Revive source: ad (default) / currency / free first. 2. Auto-dismiss on countdown end: yes (default) / no.

## Checks
Ad failure does not revive; countdown stops during the ad; both buttons reachable at 20:9; no-thanks never overlaps revive; contract lints.
