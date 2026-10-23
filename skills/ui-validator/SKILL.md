---
name: ui-validator
description: Check a UI prefab numerically for structure, overlap, safe area, text fit, raycast, 9-slice, missing references and more at several aspect ratios, with reasoned exceptions. Use after building or changing any popup, HUD or page, before screenshots.
---

# UI validator (static, from prefab YAML)

Replaces "does it look right?" with numbers (report 17 sec 5). Run it after every build/edit; it is fast, read-only and works with the Editor closed.

`py -I <skills>/ui-validator/scripts/ui_validator.py <file.prefab> [--kind popup|page|hud|canvas|none] [--hud] [--project <unity-project>] [--reference ref.prefab] [--exceptions qa/ui-exceptions.json] [--dump-rects texts.json] [--ref 1920x1080] [--banner 200] [--margin 24]`

It resolves each RectTransform to a rect (anchors, pivot, offsets) and re-evaluates at 1920x1080, 2400x1080 (notch + gesture bar simulated: 132 px sides, 63 bottom) and 1600x1200 with CanvasScaler Expand. Exit 1 on any FAIL. `--project` enables the guid checks (9-slice borders, missing sprites/scripts); `--hud` enables banner clearance and the free-centre check.

| Rule | Level | Meaning |
|---|---|---|
| UI-STRUCT | FAIL | `--kind popup/page/hud`: prefab root has exactly one child `Root`, stretched with zero offsets, no Graphic. `--kind canvas`: Overlay, Scale With Screen Size, match mode Expand |
| UI-OVERLAP | FAIL | two interactive rects (not parent/child, shrunk 4 px) intersect; inactive state panels skipped |
| UI-SAFE | FAIL | interactive or text rect leaves the safe area inset by the margin (backgrounds, dims, blocks, viewports exempt by name) |
| UI-BANNER | FAIL | with `--hud`, an element sits below the bottom clearance |
| UI-CHILD-EQ-PARENT | FAIL | a graphic child has the same rect as a graphic parent (double frame); `Root`, backgrounds, viewports exempt |
| UI-RAYCAST | FAIL | non-interactive graphic has Raycast Target on; panels containing buttons, scroll/slider/toggle parts and blockers allowed |
| UI-9SLICE | FAIL / WARN | sprite with an importer border must be Image Type Sliced (FAIL); rect below the border sum is a WARN (Unity shrinks borders) |
| UI-MIRROR | FAIL | text mirrored by a negative X scale on itself or an ancestor |
| UI-MISSING | FAIL | script reference with fileID 0; with `--project`, script or sprite guid unknown to the project |
| UI-REF-MATCH | FAIL | with `--reference`: element missing, centre/size off by more than 2 px, sprite or font size differs |
| UI-TEXT-FIT | FAIL | static estimate says text cannot fit inside its rect at the configured Auto Size minimum, or it uses Overflow without Auto Size |
| UI-CONTENT-CONTAINMENT | FAIL | content/control child leaves its padded parent content area or overlaps a content sibling; named decorative background/frame/glow layers are exempt |
| UI-FONT-MIN | WARN | autosize minimum font under 18 |
| UI-TOUCH | WARN | interactive target under 88 px |
| UI-SPACING | WARN | 3+ interactive siblings with gap spread over max(8 px, 15%) |
| UI-ICON-LABEL | WARN | side-by-side icon + label: icon height / (0.7 x font) outside 1.2-2.2, or not vertically centred within 3 px |
| UI-CENTER-FREE | WARN | `--hud`: interactive/text inside the central 40% x 40% |
| UI-CONTRAST | WARN | measured from a screenshot, see `ui-visual-qa` (`--dump-rects` supplies the text rects) |
| UI-UNKNOWN | INFO | element under a layout group / size fitter: size needs the runtime validator |

Degenerate rects (zero or negative size) and inactive objects are skipped by the soft/size rules; use `include_inactive` to check state panels.

## Exceptions
`qa/ui-exceptions.json`: `[{"rule": "UI-TOUCH", "path": "Settings_Popup/Root/Board/Btn_Close", "reason": "matches the reference game", "owner": "name"}]`. An entry without a non-empty `reason` is ignored. The reference game wins over soft rules; hard-rule exceptions need the user's agreement.

## Calibration on the reference (read-only, 29 knife-tower UI prefabs at 1920x1080)
After three tuning rounds (container panels, scroll parts, inactive panels, degenerate rects, viewports, overflow mode, stacked icon/label) the remaining findings are real deviations of the reference itself: UI-STRUCT in 15 prefabs (popup trees without the standard `Root`; the user's `unity-ui` rules are the standard anyway), 9-slice sprites set to Simple (Gacha), one sprite guid that no project meta defines (`Gacha_Box_Popup`; reported, not checked in the Editor), decorative frames with Raycast Target on, soft warnings (touch 65x87 close buttons, autosize minimum 10, icon sizes). Treat them as the baseline for a new game: fix, or record a reasoned exception.

## Runtime validator (template)
`assets/Qa_UiValidator.cs.txt` is an UNCOMPILED Editor template that instantiates the prefab on a sized world canvas at the same 3 aspects, forces layout rebuilds, reads world corners and TMP preferred sizes, and writes findings JSON. It reports `UI-TEXT-FIT` and `UI-CONTENT-CONTAINMENT` as hard failures after resolved layout. It is the authoritative check for layout groups and real text sizes. Compile it via Unity MCP and compare its output with this script on one known prefab before trusting it; it uses TextMeshPro, so the UniText experiment needs its own measuring adapter. A static pass without this runtime evidence is unverified for layout groups/size fitters.

Not covered: nested prefab-instance overrides are not resolved (validate the expanded prefab or the runtime result). The static pass does not replace screenshots (`ui-visual-qa`) or the user's eye on taste.

Triage output before fixing: real (e.g. raycast left on leaf visuals) / false positive (dim backdrops, runtime safe-area insets, intentional fill-parent) / needs screenshot. Fix generated prefabs in the builder, not only the asset. Raycast sweeps clear leaf visuals only; skip graphics with interactive descendants or blocker-like names (frames, headers), or taps fall through popups.

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.
