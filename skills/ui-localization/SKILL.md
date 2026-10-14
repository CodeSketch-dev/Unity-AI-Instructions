---
name: ui-localization
description: "Localization setup for UI text: Unity Localization tables, TMP localize components, per-locale fonts, RTL, glyph coverage. Use when adding languages, new UI text, or fixing missing or unreadable glyphs."
---

# UI localization

Reference stack (knife-tower, report 07, VERIFIED): Unity Localization 1.5.12, string table `LOCALIZE` + `LOCALIZE_<code>`, 9 locales (en, vi-VN, ja-JP, ko-KR, ar-EG, ar-SA, es-MX, tr, uk-UA), RTLTMPro for Arabic.

1. Static labels carry a localize-text component (key dropdown, re-applies on locale change) AND a localize-font component on every TMP; dynamic numbers are set from code. No baked English in sprites or prefab text.
2. Locale: detect `Application.systemLanguage` once, persist the choice, wait for the async table load (the factory's ensure-initialized). A settings language list lets the player change it.
3. Fonts: one display font plus per-locale fonts (ko, ja, ar...). Material swap only behind an explicit flag. Preload glyphs for the active locale; check coverage for every shipped locale (missing glyph squares are the common failure).
4. Subscribe to locale-changed in `Awake`, unsubscribe in `OnDestroy` (`static-bus-events`).
5. Layout must survive 30-40% longer strings: autosize min/max (`ui-text-tmp`), no fixed-width assumptions.
6. Arabic: RTL text support (RTLTMPro in the reference; UniText advertises built-in RTL and is being trialled in thunder-break-egg, unmeasured and without localization so far) and mirrored alignment; verify number and punctuation order. Compare the two on a real Arabic screen before choosing.
7. Write keys in one place; fail the build or QA on missing keys (report 20 pipeline notes).

Verify with Unity MCP by switching locale in Play Mode and screenshotting key screens; say which locales were not checked.
