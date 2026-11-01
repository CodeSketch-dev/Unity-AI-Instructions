---
name: localization-pipeline
description: "Localization workflow: keys only in code, CSV export and import, lint for missing keys and length, fonts per locale, RTL, glyph preload. Use when a GDD needs more than one language."
triggers: localization, languages, translate, translation, strings, i18n, ngon ngu, dich
---

# Localization pipeline

Components and key naming are in `ui-localization`; text components in `ui-text-tmp`. This is the process.

1. Strings enter only through localize keys (constants), never baked into prefabs.
2. Export the table to CSV: key, source text, context, max length, screen.
3. Translate (human or model) with a glossary: brand and currency names stay, placeholders such as `{0}` preserved.
4. Import back; fallback chain locale then English.
5. Lint: missing keys per locale, placeholder mismatch, length over the slot limit with an expansion factor, forbidden characters.
6. Per-locale fonts as fallback assets; preload glyphs for each font before build.
7. Arabic and other RTL: shaping via the project's RTL component, numbers and progress bars stay LTR; verify with a screenshot pass at the longest locale and at RTL (`ui-visual-qa`).

The GDD lists locales, string owner, max lengths per slot, and whether number formats localize. If a project has no localization yet, decide with the human before retrofitting; the UniText versus TMP experiment is separate (`ui-text-tmp`).

## Added from Unity official guidance (2026-11-02)
Source: official (Unity-Technologies/skills/localization), our wording; applies when the project uses com.unity.localization.
- Switch locale only through the package (`LocalizationSettings.SelectedLocale`), never hand-rolled state; keep Editor preview and runtime selection separate.
- Bind text with `LocalizeStringEvent`; persistent listeners must target a method on a UnityEngine.Object (lambdas are not serializable). A configured-but-unbound component is a dormant defect: check each one.
- Qualify `UnityEngine.UI.*` types in editor builders to avoid name clashes; recompute layout after text changes with `LayoutRebuilder.ForceRebuildLayoutImmediate`.
- Wrap lookups in one static helper so existing code changes minimally; when mapping existing strings to keys, match the longest strings first so short ones ("NO") do not hit inside long ones.
- CJK: TMP essential resources must be imported first; use dynamic fallbacks (see `tmp-font-optimization`).
- Table completeness check before done: every key exists in every locale, no empty entries, then run the Addressables content build and switch locale in the Editor to confirm.
