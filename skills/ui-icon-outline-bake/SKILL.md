---
name: ui-icon-outline-bake
description: Use when UI icons look thin/inconsistent next to the plates: bake one thick uniform navy outline into every icon PNG (idempotent ledger, layouts do not move, generated C# skip-list for any runtime outline ring).
triggers: icon outline, vien icon, outline icon, icon mong, bake outline, icon dong bo, outline dong nhat
---
# Bake a uniform outline into icons
`python -I icon_outline_bake.py --ledger <project>/docs/ui-style/icon_outline_ledger.json --cs <project>/.../Dig_Ui_IconOutlineBaked.cs --ratio 0.055 "<icon globs>"`
- Outline = same navy as the plate outline (8,13,28), width = ratio x longest side (>= 3 px), anti-aliased from a 3x distance field: identical thickness on every icon and curve.
- The icon content is scaled down so icon + outline fit the ORIGINAL canvas: sprite size, ppu and layouts do not change.
- Idempotent: the ledger (file -> hash or "skipped") prevents double outlines; opaque rectangles and >640 px art are skipped. Re-run after adding icons; never re-bake a ledgered file (restore it from git first if you must redo it).
- The generated C# HashSet lets runtime outline helpers (a scaled dark copy behind the icon) skip baked icons, otherwise the rim is doubled.
- Scope: icon folders only (ic_*, icon_*, egg thumbnails); not plates, backgrounds, pets, atlas sheets. Also bake atlas copies of the same icons (e.g. a UiBaked folder) or the old thin art keeps showing.
- Verify in a Play screenshot: icon rim looks as thick as the button rim; icon + label rows stay centred.

- Mixed icon families: one row icon from an old/reference atlas next to new-kit icons reads grey and dull. Check every row of a screen with a sprite-source dump (sprite.texture.name per icon) and replace the stragglers in one pass.
