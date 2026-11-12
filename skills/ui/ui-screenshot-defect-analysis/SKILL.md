---
name: ui-screenshot-defect-analysis
description: "Use whenever the owner sends a UI screenshot or says something looks wrong/ugly/dirty: produce a numbered defect table from the image BEFORE touching code (overlap, padding, alignment, missing text, outline family, words-vs-icons, clipping, contrast), fix every row, re-capture, compare."
triggers: screenshot, anh chup, nhin xau, ban mat, lech, de len nhau, mat text, khong align, padding, ui xau, senior review, defect table, sai o dau
---
# Screenshot defect analysis (owner 2026-11-10: "I sent you the picture and you still do not know what is wrong")
## Self-critique that created this skill (what the agent did wrong all day)
1. Reacted to ONE crop at a time and patched that sprite; never looked at the whole screen or the other screens that use the same family.
2. Never listed what was wrong in the owner's image; fixed what it already knew. The owner had to repeat the same complaint 6+ times.
3. Measured outline in sprite pixels, not canvas/screen units: families with different ppu looked different (buttons 3.5, rail 3.2, old tabs/pills 2.0-4.5 units).
4. Did not inspect the runtime path: the same texture was wrapped with two ppu values (a cache rebuilt the sprite with the default ppu), so two buttons with one texture had different outlines.
5. Guessed causes (underlay, atlas padding) and shipped global changes before reproducing; read the reference project (Break and Steal) only after being shouted at.
6. Restructured a prefab without grepping the consumers (NullReference on a Find path), edited .meta files that an importer overwrites, wrote a border in the wrong order (L,B,R,T), and reported "done" without opening the other screens.
7. Skills existed (padding rule, HLG rule, icon-not-word rule) but were not applied: nobody ran the checklist on the picture.
## The pass (mandatory, output a table first)
For every screenshot: view it at full size, then zoom the busy areas. List each defect as `# | where | what | rule | fix`:
- OVERLAP: image over image (ribbon over icon, badge over text, button over card edge), text over a border/lip, anything touching its parent edge (padding < 12 px).
- ALIGNMENT: label/icon groups centred in the free gap; same baseline across siblings; equal gaps; column/row edges aligned.
- MISSING/EMPTY: badges or labels with no text, zero-size text, text same colour as its background, clipped glyphs.
- WORDS vs ICONS: currency/amount rows use number + icon, never "gems"/"cash" words; coloured numbers.
- FAMILY CONSISTENCY: outline thickness in CANVAS units identical for plates, cards, tabs, pills, icons (run `ui-sprite-audit/family_audit.py`); same corner radius, shadow and lip style; no leftover old-style sprite next to new ones.
- CLIPPING: scroll viewports cutting a card at the first/last item, content outside safe area/banner band.
- CONTRAST: yellow on yellow, white on pale, tiny text on busy art.
Then: fix ALL rows (shared source, not per instance), dump the live Sprite/Image values for suspicious instances (ppu, border, rect, scale), re-open EVERY screen that uses the touched family, capture, and show before/after. Report the table with each row marked fixed / not fixed (+why). Never say done with rows open.
