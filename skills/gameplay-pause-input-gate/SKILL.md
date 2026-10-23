---
name: gameplay-pause-input-gate
description: "Pause with Time.timeScale 0 while waiting for a player action that a physics step must run: resume on the press, not the result, or the game freezes. Use for tutorial pauses and freeze-until-tap prompts."
---

# Pause that waits for a gameplay input

Why: a tutorial or prompt that sets Time.timeScale = 0 and then waits for the player to perform an action deadlocks when that action is processed in a physics step (FixedUpdate, kinematic motor). The step never runs at timeScale 0, so the 'done' event never fires and the game stays frozen.

## Rule
Resume time on the PRESS (an Update-time input event), not on the RESULT of the action.

## Steps
1. Add an event raised from the input component's Update when the key or touch is pressed (after its locked/blocked checks, so it matches the cases where the action would really run). Update still ticks at timeScale 0.
2. In the paused step: subscribe, wait until 'result happened OR press happened', unsubscribe, set timeScale back to 1, then hide the prompt. Also unsubscribe and restore timeScale to 1 in OnDisable so a disabled tutorial never leaves the game frozen.
3. The motor keeps the buffered request while paused (its buffer timer only advances during simulation steps), so the first step after resume performs the action. Check this assumption in the project's controller before relying on it.
4. Verify in Play Mode: set timeScale 0, send one press, log the request flag and counters while paused (action not done, request still latched), set timeScale 1, log again (action done within a step or two). Read the result right after resume: a short jump may already have landed half a second later and look like 'nothing happened'.

## Pitfalls
- Using unscaled time for the request buffer would expire it during the pause: keep it scaled.
- Waiting for the result with a timeout only hides the freeze; fix the cause.
- Keep the event additive (static event, no behaviour change) when the input script is shared with other games.
(VERIFIED in one Unity MCP session; defaults, not hard rules.)
