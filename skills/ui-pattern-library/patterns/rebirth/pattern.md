# Pattern: rebirth (prestige)

Source: report 07 sec 4 row 13 (`MonkeyEscape_Rebirth_Popup`; Board 1146x754 in a Scale, Before/After cards 242x178 at x +-229 y110, swap 149x135, progression bar 834x83 at y-108, bottom HLG 840x115; VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Economy: `economy-progression-design`, `economy-auto-balance`.

## Behavior and hooks
- Shows current multiplier vs the multiplier after rebirth and the requirement progress. Rebirth is enabled only when the requirement bar is full (state `not_ready` disables the button and shows the missing amount).
- Confirming resets the configured progress keys atomically (currency, upgrades, position) and grants the permanent multiplier; the reset list lives in data, not scattered in code; fire `Event_Rebirth_Done`.
- A second confirm step or hold-to-confirm protects against accidents (variant).

## Binding
Rebirth config (requirement formula, multiplier curve, reset list), `Data_Rebirth` (count), the shared big-number formatter (`rule-bignumber-safety` when present).

## Variants
1. Confirm: single tap (default) / hold / second dialog. 2. Show next 3 rebirth tiers.

## Checks
Reset list complete (nothing half-reset after a mid-way kill: apply as one data write); button state follows progress; numbers use compact format; contract lints.
