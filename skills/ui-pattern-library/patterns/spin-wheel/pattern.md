# Pattern: spin-wheel

NOT mined from a reference: the reference projects have only the slot machine (`jackpot-slot`). This contract is a DESIGN (INFERRED) built from `recipe-spin-wheel` (report 20); positions and sizes are placeholders to be replaced from the target game's capture. Contract: `spec.yaml`; wireframe `mockups/wireframe.png`.

## Behavior and hooks
- Wheel asset: slots (reward, weight, colour, icon), free spin cooldown, ad spin allowance. The result slot is chosen first (weights + optional pity), then the wheel animates to it with ease-out and a small overshoot, then the reward flows (`currency-spread-fx`).
- Free spin ready sets a notify dot on the HUD entry button and a local-notification entry (`recipe-retention-timers`).
- Persist spin counts and timers before the animation; never re-roll after a quit.

## Binding
`Wheel_Asset`, `Data_Wheel` (free spins, last free time, ad spins today), reward service, audio (tick per slot).

## Variants
1. Slots: 8 (default) / 6 / 12. 2. Ad spin: 1 extra per day (default) / unlimited with cooldown. 3. Honest odds label shown / hidden (designer choice).

## Checks
Pointer lands on the pre-chosen slot at all frame rates; spin buttons disabled while spinning; free timer honest after a clock change; contract lints; `ui-validator` clean.
