# Reference archive and portability

## Current guidance
- [Reference profile](reference-profile.md): measured source values and configurable input modes.
- [Input verification](input-verification.md): first-tap, cancel, disabled and raycast acceptance checks.
- [Portable view](reference-implementation/QuestFocusPointer.template.cs.txt): scene-authored serialized-reference example. Source text only; compile and exercise it in the adopting project.

## Historical evidence - do not copy as current defaults
`prefab-dumps/` contains Knife Tower source hierarchy/material snapshots. Preserve them as provenance. Their transparent blockers describe a dismiss/block mode and must not silently reappear in pass-through mode.

`images/` includes earlier Dig for Egg iterations, including rejected placements and an owner-specific fingertip adjustment. Filenames containing `before` or `too-far` are failure examples. Even `final` records approval at that time, not a shared global design rule.

`reference-implementation/Quest_FocusMessage.dig-for-egg.cs.txt`, `Ftue_KtPresenter.dig-for-egg.cs.txt` and `Quest_FocusPointer.dig-for-egg.cs.txt` are historical full-game examples with project dependencies. They may use raw pointer polling, runtime hierarchy construction, a different dim/hand profile or first-tap dismissal. Do not treat them as safe current production templates. Follow the main skill and current project's accepted-action/scene-authoring rules instead.

`assets/Hand.png` is the archived reference hand art. Reusing it still follows the target project's asset provenance rules; this archive does not certify distribution rights.
