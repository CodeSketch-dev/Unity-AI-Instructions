---
name: spec-pdf-extract
description: Extract text and DEMO images from a PDF/sheet spec so nothing is missed. Use whenever the user attaches a PDF/sheet spec (GDD, ad script) before planning or coding.
---

# Spec PDF extract

A spec sheet exported to PDF hides half of its meaning in the DEMO column (screenshots) and in note columns. Reading only the text makes UI and flow wrong, and the user will say "read the description and the demo carefully".

## Steps
1. Run `python -I <skill>/extract_pdf.py "<pdf>" <project>/docs/<spec>-demo` (install once: `pip install --user pypdf pillow`). `Read` on the PDF alone returns nothing usable and `pdftoppm` is usually missing on Windows. On Windows set `PYTHONIOENCODING=utf-8` when printing Vietnamese text.
2. Read `text.txt`, then open EVERY extracted image with `Read`. Each image is a requirement: layout, art style, icons, labels, state variants (done / current / locked), countdown badges, helper text under buttons.
3. Build a table: row (placement) -> text rule -> demo image -> remote-config note -> your decision. A "Remote Config Note" column means the numbers must be config fields, not constants.
4. List what the demo shows that the text does not say (icons, tags, counters, helper text) and what the text says that the demo cannot show (conditions when NOT to show). Implement both.
5. Record unclear rules in the project feedback notes and ask the user ONE batched question only for real design forks (scope, meaning of a term). Mention images the user said they sent but that did not arrive.
6. Out-of-scope rows (later version, missing game system) are listed back to the user, not silently dropped.

## Pitfalls
- The user's later chat message overrides the sheet wording (example: "the countdown always plays the interstitial, claimed or not"). Read helper text under buttons ("AD PLAYS IN 3S") as behavior, not decoration.
- Keep the extracted images in the repo docs folder so later sessions and other agents can see the spec.
