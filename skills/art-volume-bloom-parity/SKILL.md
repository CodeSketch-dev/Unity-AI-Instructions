---
name: art-volume-bloom-parity
description: "Diagnose glare on ported models: compare the scene's post Volume with the reference's before touching materials or runtime exposure hacks; find leftover root renderers after a model swap. Use when pets or characters bloom too much."
---

# Volume and bloom parity

Why: ported models that 'glow too much' are usually blamed on materials, then patched with runtime exposure hacks that darken everything and still miss cases. The real cause was a post-processing Volume that the reference never had.

## Steps
1. **Compare the scene Volume with the reference scene's Volume first.** Read each profile's components and overrides (Bloom threshold, intensity, clamp, scatter; Color Adjustments) through the Volume API. A reference with Color Adjustments only has no bloom at all.
2. **Check where the profile reference lives.** Plain scene object: change it in that scene only. Prefab instance or shared profile asset: other games or scenes use it too, so assign a different profile on this scene's volume and leave the shared asset untouched. Check other scenes' profile references before touching any shared one.
3. **Fix the volume before the models.** With the reference's volume, ported materials render like the reference. Only then judge per-model glare.
4. **List per-model facts, do not guess**: material asset path, shader, emission strength, HDR colours, vertex-colour brightness. Models that share one material cannot be fixed by editing that material.
5. **Look for leftovers from a model swap**: when a script replaces a model with another prefab, an old renderer on the ROOT object survives (only children are removed) and draws on top of the new model. Disable that renderer in the source prefab.
6. **Runtime exposure/emission overrides** (property blocks that dim every model) are a symptom patch: once the volume matches the reference they only make models darker than the original. Report them and let the user decide; do not delete silently.

## Save safely
Do the scene save only after the user agreed to the specific change, stop Play Mode first, then read back the profile path and the components list.
(VERIFIED in one Unity MCP session; defaults, not hard rules.)
