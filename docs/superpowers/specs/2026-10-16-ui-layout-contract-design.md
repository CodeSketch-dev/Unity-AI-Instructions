# UI Layout Contract Design

Status: approved by the user on 2026-10-16.

## Intent

New Unity UI must be generated from a containment-first contract so TextMeshPro labels, buttons, boards, frames and sibling controls do not overlap or escape their intended parent. The result must prevent recurring repair prompts for text overflow, poor button centring and baseline drift.

## Goals

- Make TMP Auto Size the normal label policy, with role-specific minimum and maximum fonts and insets.
- Make button growth conditional on the parent content area's padding and on non-overlap with siblings.
- Require icon and label to be centred as one group inside a button, with a shared TMP baseline adjustment rather than per-prefab offsets.
- Turn static detectable text overflow, label/content-bound escape and interactive sibling overlap into validator failures.
- Require runtime validation after Unity layout rebuild at supported aspect ratios, because prefab YAML cannot authoritatively resolve layout groups.

## Non-goals

- Do not change reference-driven designs that intentionally overlay decorative background/frame layers.
- Do not silently truncate, abbreviate or alter user-facing text when it cannot fit.
- Do not hand-author Unity prefabs or make a universal replacement for a project's existing UI architecture.

## Contract

Each content-owning parent defines a padded content area. A button may grow from its TMP/icon preferred size only while its full bounds remain inside that area and do not intersect another interactive/content sibling. TMP labels are no-wrap, Auto Size is enabled, and their resolved bounds must stay inside their owning button's text inset. Frame and Board graphics may be layered as decoration, but controls and text may not cover their borders or unrelated siblings.

If a label does not fit at its configured minimum font and the button cannot grow safely, generation stops with a hard validation failure and requests a design/content decision. It must not rely on TMP Overflow, overlapping RectTransforms or manual per-label baseline nudges.

## Acceptance evidence

1. The relevant UI skills instruct generation to create padded content containers, use Auto Size and centre icon+label groups.
2. The static validator returns FAIL for detectable label overflow and containment violations, while preserving legitimate decorative layers.
3. The runtime editor validator checks resolved TMP preferred bounds, layout-group results and sibling intersections at all supported aspect ratios.
4. Focused validator tests and strict skill lint pass.
