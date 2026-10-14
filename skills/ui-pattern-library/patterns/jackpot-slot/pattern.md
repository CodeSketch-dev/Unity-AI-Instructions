# Pattern: jackpot-slot

Source: report 07 sec 4 row 4 (`Jackpot_Spin`, items, paytable; sizes VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Related: `recipe-spin-wheel` (wheel variant), `economy-progression-design`.

## Regions
Machine art 1413x814 (y+76), reel window 821x413 (y+146), one spin button 275x110 (`Spin_Free` and `ButtonIAP` share the slot, state swap), paytable button 91x103 opening a left panel 286x480, lever 133x260 on the right, close 135x135. Result overlay (`Result_Cup / Result_Speed / Result_Outfit`) plus a shower FX on the window.

## States
| State | Behavior |
|---|---|
| idle | free spin: shake loop (freq 24, rest ~1.2 s); paid: scale yoyo InOutSine |
| spinning | reels animate; buttons disabled |
| result | prize overlay + fly-to reward; `Spin_Free` -> `ButtonIAP` swap when free spins are used |
| paytable | side panel with prize rows and odds label |

## Behavior and hooks
Outcome is decided first (weights + pity, `economy-auto-balance` tunes them) and applied once; animation only displays it. Free spin cooldown from the data block; paid spin via IAP/ad (`unity-iap-port`, `ads-popup-flow`). Honest paytable labels the real odds the designer chose.

## Binding
`Jackpot_Asset` (slots, weights, prizes), `Data_Jackpot` (free spins, last free time, pity), audio configs, reward flow.

## Variants
1. Spin source: free+ad (default) / currency / IAP. 2. Wheel instead of reels (`spin-wheel`). 3. Jackpot progressive counter.

## Checks
Result survives a mid-spin app kill; free-spin timer honest after clock changes; paytable closes with Back; contract lints; `ui-validator` clean (the machine art is a container).
