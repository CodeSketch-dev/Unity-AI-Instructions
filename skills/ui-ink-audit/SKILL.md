---
name: ui-ink-audit
description: Use automatically in EVERY Unity project, on any UI edit, Play test or screenshot: an Editor watcher audits the whole game's UI (every popup, HUD, shop, minigame screen) by pixels - icon+text centred on the MEDIUM button face, titles on their colour band, no overlaps - and reports [InkAudit] FAIL lines to fix.
triggers: align, canh giua, lech, button, icon text, hatch, claim, price, pill, title, header, popup, hud, shop, shadow, outline, ink, screenshot, ui audit, play test, qa
---

# UI ink audit (whole game, automatic)

Rects lie. Buttons are sprites with bands top to bottom: dark OUTLINE, LIGHT highlight, MEDIUM face, SHADOW lip, OUTLINE. The icon + label pair is centred on the MEDIUM face only, horizontally and vertically (tolerance 2 px). A header title is centred on its colour band (`ui-title-band-centering`). A row of buttons is centred on its board.

## Rule 0 (construction)
Every button / pill / frame holding icon + text is ONE `HorizontalLayoutGroup` (icon first, label second, MiddleCenter, Capline text, spacing 5/10/15). Top/bottom padding carries the light/shadow asymmetry. Never a hand-positioned icon beside a stretched label. Badges ("x2", dots) overhang on purpose and are excluded from the pair.

## It runs by itself (no prompt, any project)
`Qa_InkWatcher` (Editor, `[InitializeOnLoad]`) watches what the player sees in Play Mode: the open popups, or with no popup the set of visible buttons of the active scene. When that set changes and settles it dumps the screen (`Qa_InkDump`), captures a screenshot and runs `ink_audit.py`. Each distinct violation is a Console warning `[InkAudit] <screen> FAIL ...` (once per session) and is appended to `Temp/InkAudit/report.txt`; a screen with none logs `[InkAudit] <screen> -> 0 fail`.

## It also fixes itself (zero effort, zero tokens)
Every FAIL with a source prefab is written to `Temp/InkAudit/fixes.json` and applied at once (also while Play runs; leftovers when Play stops) by `Qa_InkFix`: HLG padding for buttons with a group, child offsets for plain label buttons, label offset for header titles; only failing items are touched, each target at most twice (then it logs "needs a manual look"). Toggle: menu Tools/Qa/Auto-apply ink fixes after Play. Gradient / textured buttons and frames use the button rect as the face; tiles whose icon overhangs the label (HUD) only check the horizontal centre; currency bars, joysticks and badges are skipped (own contracts). Runtime-built UI (no prefab) is reported but cannot be auto-fixed.

Install: nothing to do. `sync.bat` copies the Editor scripts (`templates/unity-editor/AiQa/*.cs.txt`, namespace `AiQa`) to `Assets/_AiQa/Editor/` of every Unity project that has uGUI/TMP (and removes older hand-copied `Qa_Ink*.cs`), places `ink_audit.py` under `<project>/.claude/skills/ui-ink-audit/`, and registers the agent notifier hook (`ink_audit_notify.ps1`). New projects get it on their first sync. Needs `python` + Pillow on PATH.

## The agent is told automatically
When a screen has FAILs the watcher writes `Temp/InkAudit/pending.txt`; the hook `ink_audit_notify.ps1` (PostToolUse / UserPromptSubmit / Stop) hands it to the agent once, so the agent fixes the rest without the user saying anything. Nothing pending = the hook prints nothing and costs nothing.

## What the agent must do (every task, every Play test, every autoplay)
1. During and after any Play run read the Console for `[InkAudit]` (e.g. console-get-logs Warning). Open popups the test never reaches (offline/welcome, daily, shops, treadmill, bag, pets, eggs, every minigame HUD) so the watcher sees them; a screen nobody opened is NOT audited.
2. Every FAIL line carries the fix (HLG padding units = px*2/scale, or move title N units). Apply it on the SOURCE prefab (stop Play first, animated components off while saving), re-run, repeat until `0 fail` for every screen touched. Treat a FAIL seen in any test as a bug of this task, not a note for the user.
3. Manual run: `Qa_InkDump.Run(json)` + `ScreenCapture.CaptureScreenshot(png)` then `python ink_audit.py png json`.
4. Report the screens audited with their fail counts. If python/Pillow is missing, say so and fall back to `ui-title-band-centering` measurements.

## Limits (say them, do not hide them)
- Face = most common colour of the button centre: gradient/textured buttons need an eye check on a zoomed crop.
- Ink = near-white text + visible icon pixels; coloured text needs the colour added in `ink_bbox`.
- `ScreenCapture` covers overlay canvases; camera canvases need a game-view capture.
