---
name: tmp-shader-alpha-clip-fix
description: Use for ANY TextMeshPro work (new project, package update, text looks smeared/dark behind glyphs, outline artefacts): patch the TMP SDF shaders' alpha clip line, guard it with a test, and follow the careful-TMP checklist.
triggers: textmeshpro, tmp, text mesh pro, alpha clip, clip shader, vet den sau chu, text bi den, outline text, tmp shader, font sdf, chu mo
---
# TextMeshPro: careful checklist (owner 2026-11-10)
## 1. The shader patch (do it on every project, re-check after every TMP update)
In `Assets/TextMesh Pro/Shaders/TMP_SDF.shader` and `TMP_SDF Overlay.shader` (and any other TMP_SDF* variant that has it) replace
`alphaClip = alphaClip / 2.0 - ( .5 / scale) - weight;`
with
`alphaClip = max(alphaClip / 2.0 - ( .5 / scale) - weight, 0.01);`
Reason: the stock value can go negative for thick outline + dilate, so the outline pass is never clipped and a dark halo / smear shows behind (and around) glyphs. Owner confirmed this removed the smear in another game. Mobile variants use a different clip (`clip(c.a - 0.001)`), leave them.
Guard it with an EditMode test that fails when a TMP package update restores the stock line (template: `DigTmpShaderPatchTests.cs`, scans Assets/TextMesh Pro/Shaders/TMP_SDF*.shader).
## 2. Material rules
- ONE shared outlined UI material; outline + face dilate sum well below the SDF range of the font (reference 0.30 + 0.28). Outline 0.5 + dilate 0.5 on a padding-9 font bleeds into neighbouring glyphs.
- Never raise `atlasPadding` on an existing dynamic font in place (dark rectangles behind every text); create a new font asset with padding >= 25% of the point size and compare screenshots.
- Underlay: only with enough padding; test before enabling globally.
## 3. Before reporting any text change
Zoom screenshot (4x) of small and big text in Play; look for halo, clipped glyph tops, neighbour fragments; change ONE material/shader suspect at a time and revert on no improvement. See also `tmp-font-optimization`, `ui-text-tmp`.
