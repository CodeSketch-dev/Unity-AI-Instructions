# Default shrink-hole profile

Provenance: read-only source prefab/hierarchy archive of the studio reference game (see PROVENANCE.md), inspected again on 2026-11-03. These values describe that reference's focus style; runtime input delivery is a separate contract. An exact-match request still requires current MCP inspection and screenshots of both projects.

| Part | Reference value |
|---|---|
| Overlay order | Reference game: child of the popup canvas overlay container (popup canvas sort 12506), re-sent to last sibling on each focus; transition canvas (20000) above. A project value of 310 above popups at 300 was used in an earlier port. Adapt to the actual project orders |
| Root rect | Centered on target's own rect plus explicit extension |
| Hole appear | offsets +/-1000 -> 0, 0.35 s OutSine |
| Dim | black alpha 0.9607843 |
| Top | anchor (0.5,1), pivot (0.5,0), size 3500 x 3500 |
| Bottom | anchor (0.5,0), pivot (0.5,1), size 3500 x 3500 |
| Left | anchors (0,0)-(0,1), pivot (1,0.5), size 3500 x 0 |
| Right | anchors (1,0)-(1,1), pivot (0,0.5), size 3500 x 0 |
| Hand anchor | (0.8,0.3) relative to target-sized box |
| Hand pivot | (0.1,0.78); fingertip of archived art |
| Hand size | 134.35 x 127, Preserve Aspect |
| Hand motion | scale 1 -> 1.1, 0.5 s each direction, yoyo forever |
| Hand orientation | Fixed, up-left pointing; no rotation, mirroring, sway or translation |
| Gold rings | Absent; add only as a recorded local deviation |
| Inline message | Fade 0.3 s; reference pointer message is optional, above focus top +4 px |
| Separate notice profile | Black rounded plate, alpha about 0.85, one localized instruction + optional icon |

The original Pointer/Icon nesting includes its own offset. Do not flatten that nesting and then claim pixel parity just from matching the parent's anchor. Use the source dump and screenshot to compare actual visible fingertip position; update sprite pivot only when the art changed.

## Input modes
Default gameplay focus passes through: all dim/hand/ring graphics and transparent center Images have raycasts off. The target receives the original gesture and performs its action. The original archived prefab includes transparent blockers; those are evidence of an optional dismiss/block mode, not requirements to copy into pass-through mode.

If a modal tutorial intentionally blocks outside touches, retain the four outside hit areas but keep the center open. A center blocker that dismisses without executing the target uses up the first tap and fails the direct-action acceptance criterion. Do not fix that by blindly invoking the target as well as allowing pass-through.

## Notice placement and world arrow
Place the notice above the target when space permits; otherwise choose a free side inside the safe area. Measure clearances against actual art/ads/controls. Do not turn a single game's travel button placement into a shared global rule.

For a world arrow, the archive's line uses two points, width about 1, transparent material with Cull Off/ZWrite Off and scrolling red arrow art. Material properties, terrain-height sampling, reach distance and endpoints belong to the adopting project's gameplay contract.

## Reference scope
The [portable view](reference-implementation/QuestFocusPointer.template.cs.txt) shows input-safe serialized wiring; it is not an Editor builder or a pixel-identical copy. Archived game examples remain historical and may contain stale dependencies/raw-input dismissal. Verify every adopted path in the current project.
