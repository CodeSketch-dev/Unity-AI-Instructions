---
name: localization-pipeline
description: "Localization workflow: keys only in code, CSV export and import, lint for missing keys and length, fonts per locale, RTL, glyph preload. Use when a GDD needs more than one language."
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
