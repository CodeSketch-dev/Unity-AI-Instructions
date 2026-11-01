---
name: tmp-font-optimization
description: "TextMeshPro font and text performance: static main font plus dynamic fallbacks, padding ratio, atlas size, autosize cost, world text, CJK. Use when TMP atlases bloat memory, glyph weight differs, text spikes CPU or a multilingual build is large."
triggers: tmp font, textmeshpro, font atlas, sdf, fallback font, dynamic font, cjk, autosize cost, text spike, font memory, build size font, chu bi mo, atlas font, font dong, toi uu chu, da ngon ngu
---

# TMP font and text optimization

Source: official (Unity-Technologies/skills/optimize-text-mesh-pro), re-written; items marked [ours] are our practice.

## 1. Triage first
Ask which symptom: atlas memory, glyph weight/blur, CPU spike on text change, build size, Latin+CJK misalignment, style variants. Measure before changing (Memory Profiler for atlases, Profiler for Canvas.BuildBatch / TMP rebuild).

## 2. Rules
- Main font = STATIC asset with every needed glyph baked. Everything else (CJK, symbols) = DYNAMIC fallbacks, atlas 512-1024.
- Every dynamic font asset: enable `Clear Dynamic Data On Build`, else glyphs baked while testing in the Editor ship.
- Keep Padding / Sampling Point Size ratio identical across main and fallbacks (10% is safe). A mismatch gives different stroke weight on one line.
- Sampling size: Latin about 70-90, CJK about 36-50.
- Font asset Scale must be 1 (an imported 0.9 breaks point-size maths).
- Styles (italic, outline, glow) = material presets of one font asset, not duplicated font assets.
- Sprite-asset source textures use Texture Type Default, not Sprite (faster load on mobile).

## 3. CPU
- AutoSize re-fits on every string change: fine for static localized labels, wrong for live counters. [ours] With our auto-fit helper, set text only when the value changes and fit once after a locale change.
- Parent often-changing UI text under its own Canvas so rebuilds stay scoped. Split static and dynamic canvases.
- World-space text: use `TextMeshPro` (not `TextMeshProUGUI`) and no extra world Canvas.

## 4. Multilingual builds
- Evaluate `Atlas Population Mode = Dynamic OS` (TMP 3.2+ preview) to drop shipped CJK fonts: Android falls back to Noto, iOS uses per-language CJK families. Test on a real device; the Editor uses the project font.
- Misaligned Latin+CJK on one line: show ascender/descender overlays (TMP_TextInfoDebugTool from Examples & Extras) and adjust the font asset ascender/descender.
- Memory Profiler in the Editor includes the raw .ttf; untick `Include Font Data` on the font import to compare with a device.

## 5. Checks
- List TMP font assets as a table: mode (static/dynamic), atlas size, fallback chain, padding ratio, Scale.
- Play a screen in every shipped language and screenshot (see `ui-localization`, `ui-layout-audit`).
- Build once and compare player size / Memory Profiler snapshot before and after. State when not measured on device.

## Pitfalls
One giant dynamic atlas for all languages; forgetting Clear Dynamic Data; world text on UGUI; autosize on timers.
