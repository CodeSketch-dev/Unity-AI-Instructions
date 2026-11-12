---
name: ui-shop-card-frame-gen
description: "Use when generating shop / pack / offer card frames (KT sunburst pack look) with Codex image_generation: approved style spec, colour family, prompt, magenta cut, audit false positives, kit import."
triggers: shop card frame, pack frame, card frame, sunburst, frame pack, gen frame, khung shop, khung card, khung pack, frame shop xau
---

# Shop card frame generation (owner-approved look)

Why: flat rarity cards with an inner frame or header band read as "old junk" and do not sell; the owner approved this sunburst family at first try. Reproduce it exactly instead of re-inventing.

## Style spec (do not drift)
- Portrait rounded rect, aspect ~0.72 (e.g. 404x562), radius ~8 % of width. No pill, chamfer, tab, header band, inner frame, second border or outer shadow.
- ONE thin near-black navy outline (#151a2a), ~1.5 % of width, identical on every card.
- Saturated vertical gradient (lighter top) + darker 3-4 % bottom lip following the corners.
- Soft 16-20 ray SUNBURST from a white-hot glow at 40 % height: the hero item sits there.
- Faint tone-on-tone doodles of the game's own items (~8 % contrast, never busy) + two small white sparkles in the top corners. No text.
- Family of 7: gold #FFC31F->#F08A00, purple #B45CFF->#8A2BE2, blue #4FA8FF->#2F6BFF, green #6EE05A->#2FAE3A, coral #FF7A6B->#F0435A, teal #3FE0E0->#13A9C9, rainbow (pink, gold, mint, sky).

## Steps
1. Copy `prompt_template.txt`, replace the doodle list with the game's items, attach 1-2 reference pack frames (the owner's own reference game) with `-i`.
2. Run Codex on stdin: `cat prompt.txt | codex exec -m <luna slug> -c model_reasoning_effort=low --disable hooks --disable codex_hooks --skip-git-repo-check -C <raw dir> -s workspace-write -i ref1.png -i ref2.png -`. Take the exact slug from `~/.codex/models_cache.json` (`"slug"`): bare `luna` and invented versions are rejected on a ChatGPT account (400 model_not_found).
3. Cut with `cut_cards.py` (dry run first): the key is the colour distance to pure #FF00FF, not "min(r,b)-g" (that deletes purple and pink cards); the crop bbox uses alpha > 200 so stray soft pixels never shrink the card.
4. Look at a contact sheet and an 8x corner crop. Then `ui-sprite-audit/sprite_audit.py --kind board --max-long 600`.
5. Import through the kit manifest (border all sides ~44 at 404 wide, L,B,R,T), swap the WHOLE card family in one pass, Play screenshot at real size.

## Audit false positives on these cards (judge by the crop, record a Ruling)
- "outline uniform" spread 14-16 px: the dark bottom lip of blue / purple is counted as outline.
- "magenta fringe" on the rainbow card: its pink is real colour.
- "outline in canvas units" and the 20-36 % radius rule are button rules.

## Exceptions
Landscape / wide offer banners and tab plates are other families: keep the outline and palette, not the portrait sunburst layout.
