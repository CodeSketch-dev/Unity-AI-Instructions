# Pattern: daily-login (page)

Source: report 07 sec 4 row 2 (`Daily_Login_Popup` + item; sizes VERIFIED). Layout contract: `spec.yaml`; wireframe: `mockups/wireframe.png`. Retention logic: `recipe-retention-timers` (clock guard, reset).

## Regions
Page, not popup: title bar (~175) with `Btn_Back`, a horizontal ScrollRect (700 high) of cards, scrollbar under it. Card 431x617: thumbnail 235 (y+35), title text, value text; the Today card is larger (455x632) with an outline.

## Card states (child objects toggled, `ui-button-anatomy`)
| State | Content |
|---|---|
| claimed | dimmed + tick (102x79) |
| today | outline, claim button, shake attention loop (angle 1, 0.65 s, rest 1.1 s, scale x1.02) |
| missed | scale x1.04 pulse, recovery button (325x125, rewarded ad) |
| upcoming | normal scale 0.85 |

## Behavior and hooks
- Scroll to today's card on open (OutQuad). Claim posts `Event_Daily_Claimed`, plays the reward fly (`currency-spread-fx`), saves day index and claim time in the data block.
- HUD entry button carries a red notify dot while a claim is available (`ui-button-anatomy`).
- Reset on a clock-guarded day change; missed day offers recovery or resets the streak (variant).

## Binding
`Daily_Reward` rows (day, reward type, amount, tier), `Data_DailyLogin` (day index, last claim UTC day, claimed set), reward service, optional rewarded-ad recovery.

## Variants
1. Missed handling: reset streak (default) / recover via ad. 2. Cycle: 7 days (default) / 30. 3. Final-day big prize card.

## Checks
Scroll lands on Today at all aspects; claim once only (restart and device clock back); notify dot clears after claim; contract lints; `ui-validator` clean.
