---
name: ui-layout-audit
description: Run an automatic layout audit on the live UI in Play Mode (text centred in the free gap between icons/buttons, overlap, padding, ScrollRect margins, missing outline, tiny fonts) and fix every violation at its shared source. Use after ANY UI change, on any screenshot showing a UI defect, and before reporting UI work done.
triggers: audit, ui audit, layout audit, check ui, kiem tra ui, can giua, outline, padding, overlap, lech, tran vien
---

# UI layout audit (portable tool + loop)

The measurement step of `ui-always` / `ui-center-alignment` is automatic, so it cannot be skipped.
1. Tool: `UiLayoutAudit.cs.txt` in this skill folder (uGUI + TextMeshPro only, no project classes). If the project has no `UiLayoutAudit`/`Qa_UiAudit` class (grep), copy it to `Assets/<game>/Scripts/Editor/Qa/UiLayoutAudit.cs`, refresh/compile (Editor lock first).
2. Run in Play Mode through the Unity MCP `script-execute`: `Debug.Log(UiAudit.UiLayoutAudit.Run(popupOrHudTransform))` (null = every active canvas); read the log once.
3. It reports per text: dx vs the free gap between neighbouring graphics (or the frame edge), overlap with icons/buttons, padding L/R/T/B, font too small, NO OUTLINE; per ScrollRect: margin to the board art.
4. Loop: for every violation fix the layout at the shared source (prefab/builder/layout group/text factory, never per instance), re-run until `violations=0` or the rest is justified in the report, then take a screenshot and look at it.
5. Any screenshot, dump or user image showing off-centre/overlapping/clipped/tiny/unoutlined UI starts this loop immediately; no asking.
6. Tune thresholds only in the tool constants (MIN_PAD 6 px, MIN_SCROLL_MARGIN 12 px, MIN_FONT 14, DX_TOL 1.5 px); report the numbers.

## Make it automatic (so nobody has to remember)
- Add an Editor-only auto audit next to the tool: in Play Mode, every popup/panel that stays open ~1 s is run through the audit and violations are logged as a `[UIAudit]` WARNING with the hierarchy path (see `UiAuditAuto` pattern: `[InitializeOnLoad]`, `EditorApplication.update`, a seen/done set, a 0.4 s scan interval, no cost in builds).
- The hooks treat `[UIAudit]` in a Console read as a re-armed gate: read the Console after opening screens, fix every warning at its shared source, re-open the screen and confirm the warning is gone. A screenshot alone never proves alignment.
