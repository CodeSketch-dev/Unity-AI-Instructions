---
name: ui-text-autofit-system
description: "MANDATORY for any UI, popup, HUD, button, world-canvas or code-built text work in a Unity project. Installs/uses the automatic TMP text fitting system (auto size, padding from frames, no overflow) so text never needs manual alignment passes or reminders. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# UI text auto-fit system (automatic, every project)

Goal: the user must never have to ask for text to be fitted, padded or aligned. It is automatic: the code normalises every TMP text, and the agent verifies by measurement.

## Step 0 - install once per project (do this before any UI/text work)
1. Look for `UI_TextAutoFit.cs` in the project (`Grep UI_TextAutoFit`). If present, skip to step 2.
2. If missing, copy `assets/UI_TextAutoFit.cs` into a runtime folder (e.g. `Assets/<Game>/Scripts/Logic/UI/`) and `assets/UI_TextAutoFit_Editor.cs` + `assets/UI_AutoSweep.cs` into an `Editor` folder (adjust the `Assets/_Game` path and the report path inside UI_AutoSweep). Keep the namespace the project uses (default `Game`). Wait for compile and check the Console for errors.
3. Add the 4-line rule below to the project AGENTS.md if it is not there.

## What it does (rules enforced in code)
- Auto Size ON for every TMP text. Screen canvases: min font 10 (shrink first, never cut). World canvases: min = 50% of the authored size.
- Single-line text never wraps and NEVER shows an ellipsis ("..."): Ellipsis/Truncate/Masking overflow is rewritten to Overflow and the font shrinks to fit instead ("X2 SPEED HIT" must never become "X2 SPEED ...").
- Text that nearly fills a button / framed Image gets horizontal padding (12 px or 8% of width) so it never touches the frame or its shadow. Vertical offsets are never touched.
- Runs at runtime on the first TEXT_CHANGED of each text (covers UI built from code and spawned prefabs) AND in the Editor on every prefab / scene save. Menu `Tools/UI/Normalize Open Scene Texts` runs it on demand.
- Opt-out only via the `UI_TextAutoFitIgnore` component (tools, debug, intentionally exact sizes).

## HARD RULES - text must never leave its parent / frame (standing, no exceptions)
1. A text's RectTransform must lie INSIDE its parent's rect on both axes (no rect taller/wider than the parent, no negative-size stretch hacks). If a sibling icon shares the parent, the text rect starts after the icon (e.g. left offset = icon width + gap) so text can never overlap the icon.
2. The rendered text (`textBounds`) must lie inside the parent frame with >= 6 px margin on every side, at the LONGEST realistic string (e.g. 0/2 -> 10/10, 999.99Q, longest localised name), not only the sample text.
3. Never use ellipsis / truncation / masking to hide overflow. Shrink (auto size down to min 10), then widen the frame, then shorten the copy.
4. Never size a text with a big fixed font that only fits the sample string; always auto size with a sane max (<= the frame height * 0.6).
5. Overlays that dock to screen edges (banners, native half, tutorial hints) must not cover popup headers, tabs, currencies or buttons: compute the occupied rect from ALL visible descendants (overhanging tabs/icons/badges), not only the board, and skip/relocate the overlay when it does not fit.
6. Verification is mandatory and scripted: for every active TMP in every popup/HUD state, `ForceMeshUpdate()`, then assert (a) rect inside parent rect, (b) textBounds inside rect, (c) no overlap with sibling Graphics other than the background; report counts, fix at source, re-run until 0. Screenshots confirm but do not replace the measurement.

## One-prompt full sweep (do this by default when asked to fix UI/text, or when finishing any UI work)
The user prompts ONCE; the agent runs the whole pass without being told the steps:
1. `UI_AutoSweep.Start()` (menu `Tools/UI/Auto Sweep All Prefabs`) - instantiates every prefab on a 1920x1080 reference canvas, applies the auto-fit rules, saves fixes, writes `docs/ui-sweep-report.txt` with every remaining overflow. Poll `UI_AutoSweep.Status`; fix each reported overflow at its source (widen the rect, shorten the copy, fix the layout) and re-run until zero.
2. For each minigame scene: Play, claim startup popups, open EVERY popup / shop / board (call the popup's `Open()` or click its HUD button), and in each state run the measurement (`ForceMeshUpdate`, `textBounds` vs rect, side margins from frame >= 6 px, text centred in its button, header titles centred) plus a screenshot. Fix, repeat.
3. Scene-built or code-built HUD (Steal_Hud, Climb_Hud...) is normalised at runtime by UI_TextAutoFit; if a builder hard-codes sizes/margins, fix the builder too so the scene stays correct after a rebuild.
4. Report the final numbers (texts measured, issues left = 0) and anything intentionally ignored (`UI_TextAutoFitIgnore`).

## What the agent still does for every new or changed UI
1. Build the layout properly: icon + label as one centred group (HorizontalLayoutGroup, icon <= 50% of button height), no ContentSizeFitter fighting a layout group, money never prefixed with `$`.
2. After the change, MEASURE in Play: for each active TMP call `ForceMeshUpdate()` and compare `textBounds.size` to `rectTransform.rect`; zero overflow, centring within 1 px, text not touching the frame or its shadow (look at a screenshot too).
3. Fix at the source prefab/builder, not as a scene override. Never add per-text manual padding hacks that the system already provides.

## Project AGENTS.md snippet
```
## UI text auto-fit (standing rule)
UI_TextAutoFit normalises every TMP text automatically (auto size, padding from frames, no overflow). Never hand-fit text; build layouts correctly,
let the system normalise, then measure textBounds vs rect in Play. Read the ui-text-autofit-system skill before any UI/text work.
```

## Opt-out instead of per-frame hacks
- If an auto-fit/normalising system re-centres or resizes a text you placed deliberately (e.g. a right-aligned corner amount under a button-like card), use the system's explicit opt-out marker on that text; never fight it with `Update`/`LateUpdate` code. Re-check alignment on the live screen after the first frame, because normalisers run after your builder.
