---
name: ui-builder
description: Describe a screen as a ui-spec (layout contract), lint it, convert it to anchors, and build the prefab with an idempotent Editor builder. Use when a GDD or reference defines a screen's elements and it must come out right from one prompt.
---

# UI builder (spec -> prefab)

Why: UI that is guessed drifts or overlaps; a numbered layout contract plus a deterministic builder gives the same result every run (report 21 sec 1.4, report 17). The contract is data, the builder is code, the validator (next task) judges the result.

## Flow
1. **Write the spec** (`references/ui-spec-schema.md`): one file per screen, positions and sizes in the reference capture's pixels, elements numbered, names unique (names are the builder's keys, `ui-naming-conventions`). Unknown numbers are `?` and the fidelity drops; never invent.
2. **Lint**: `py -I <skills>/ui-builder/scripts/ui_spec_tool.py lint ui-10.yaml` (missing keys, bad anchors, missing pos/size/rect, duplicate names/numbers, text without a localization key, unknown children).
3. **Convert**: `... build ui-10.yaml --canvas 1920x1080 --out ui-10.json` converts capture px to the game's reference canvas with the CanvasScaler log blend (match 0 = width, 1 = height) and emits anchorMin/Max, pivot, anchoredPosition, sizeDelta or offsets.
4. **Build in Unity**: copy `assets/UiSpecBuilder.cs.txt` into the project's Editor folder (it is an UNCOMPILED template), compile via Unity MCP, call `UiSpecBuilder.Build(json, prefabPath)`. It finds children by name, so a second run changes nothing; it edits the SOURCE prefab and saves it.
5. **Fill the look** from tokens and patterns: sizes from `ui-design-tokens` when the spec leaves them open, structure from `ui-popup-anatomy`, buttons from `ui-button-anatomy`, text through the project's text factory (`ui-text-tmp`; Capline centring, then run `Qa_TextCenter` dry run).
6. **Verify**: screenshots at 3 aspect ratios, overlap and safe-area checks (`unity-ui`, `ui-popup-from-demo` compare loop), Console clean, builder run twice = zero diff. A look the user must judge (taste) is a checkpoint, not an agent decision.

## Conventions
- `pos` is the element's centre (pivot 0.5, 0.5) relative to the anchor point, y negative downward from top anchors; stretch anchors use `rect: {top, bottom, left, right}` insets.
- HUD elements carry a `zone` for the mechanical overlap check (`mobile-hud-layout`).
- Do not hand-write prefab YAML; builders run through Unity MCP (`editor-tool-authoring`, `rule-editor-tool-safety`).

Limits: the YAML reader is a subset (block/flow maps and lists, scalars, comments); the C# template was not compiled in this session; the numeric overlap validator is Task 11.

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.
