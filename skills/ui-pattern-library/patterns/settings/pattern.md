# Pattern: settings

Source: report 07 sec 4 row 1 (knife-tower `Settings_Popup`; sizes VERIFIED, row pitch 108-112, open 0.3 / close 0.2, dim 0.706). Layout contract: `spec.yaml` (numbered, canvas 1920x1080); wireframe: `mockups/wireframe.png`.

## Regions
Board 800x650 with title strip, three toggle rows (Music, Sound, Vibration), bottom row with Language and Home buttons, close button top-right. The language list is a sub-panel (state `language`) stretched over the Board with its own close.

## States
| State | Visual |
|---|---|
| toggle on / off | switch graphic and icon change; value is a `DataSettings` DataValue |
| language panel | scroll list of locales, current one marked; Back closes the sub-panel only |
| Home button | shown only inside a game scene; hidden on the home screen |

## Behavior and hooks
- Toggles write `DataSettings` (`SoundVolume`, `MusicVolume`, `Vibration`); audio and taptic are bound at boot (`boot-sequence-setup`), the popup only edits data.
- Language item sets the locale through the localization factory and persists it (`ui-localization`).
- Popup anatomy, Escape closes top popup only (`ui-popup-anatomy`).

## Binding
Settings data block, locale list (`Factory_Localize`), optional links (privacy, rate, restore purchases) as extra rows.

## Variants
1. Home button: in-game only (default) / always. 2. Extra rows: none (default) / rate, privacy, restore. 3. Slider instead of toggle for volume.

## Checks
All three toggles persist across restart; language change updates visible text without restart; sub-panel closes before the popup; contract validates with `ui_spec_tool.py lint`; `ui-validator` clean at 3 aspects.
