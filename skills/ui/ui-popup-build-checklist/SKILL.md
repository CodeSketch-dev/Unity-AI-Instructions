---
name: ui-popup-build-checklist
description: "Use when building or restyling ANY popup, modal, list popup or its buttons: copy the reference prefab (compact, not a full page), original Knife Tower button sprites and colour roles, BIG text, lit-face centring measured by a Play test, baked-sprite trap. Run it before the first edit."
triggers: popup, modal, list popup, cage popup, button style, knife tower button, text too small, icon not centred, nut lech style, popup nho, chu be, icon lech, can giua, giong knife tower, giong sae
---

# Popup build checklist (every item was an owner correction; do them without being told)

## 0. Pre-flight (before the first edit)
1. **Read the reference prefab, never guess.** Dump anchors / sizes of the reference popup and its row prefab (`ui-popup-from-demo/dump_prefab.py`, or grep `m_SizeDelta` / `m_text`). Note: board size, header height, row height, button size, which buttons exist per state.
2. **Compact popup vs full page follows the reference.** A "popup" is a small centred board (about 600-1000 wide, bottom 200 px of the 1080 canvas free), NOT a full-screen page with tabs. A full page is only right when the reference is one.
3. Read the open owner rules for the screen (`docs/feedback-notes.md`, AGENTS.md) and the colour/button roles below.

## 1. Buttons = the ORIGINAL reference sprites
- Use the original Knife Tower (SpeedKeyboard / shop) button sprites with their own 9-slice borders (flat rectangle, thin black outline, soft vertical gradient, darker bottom lip, crisp drop shadow). Never regenerate glossy pills, never restyle with a gloss highlight. Compare your capture next to the reference render (flat, thin outline, no shine) before anything else; "colour changed" is not "style matched". If the kit drifted, rebuild it from the reference files (`Tools/ui_kit/build_kt_buttons.py` pattern: native size, KT `.meta` border, ppu 100, hue-shift only coloured pixels).
- **Colour roles (one family per popup, 3-4 colours max):** blue = default tap, green = confirm / claim / buy, **purple = rewarded ad with the reference RED video-camera icon**, yellow = gems / premium (pink Break-and-Steal gem icon), grey = disabled, red = close. Header = KT blue. Never mix orange/green/blue for the same kind of action.
- Reward / ad / gem buttons carry the shared gentle pulse; every pressable has press scale + sfx.

## 2. Big, readable text (owner priority: big, clear, easy to read; avoid small icons/text)
- CTA text >= 40% of the button height; strip / caption labels >= 38; key numbers (price, income, counters) >= 48-54; icon >= text height. A popup that feels cramped is fixed by making the popup / buttons WIDER (or the list scroll), never by shrinking text.
- No loose strings like `LV 1   0/5 pets`: build info as grouped rows (icon + big value, then a readable second line) on a KT periwinkle plate (white outlined text never on the cream body), min 34-40.
- Never put a two-line label into a one-line label slot. Use one centred `VerticalLayoutGroup`: caption row, then `HorizontalLayoutGroup` icon + value row.

- **Cramped = widen.** When text/buttons feel tight, grow the popup width (1000-1300 on a 1920 canvas is fine, bottom 200 px stay free) and lengthen buttons; never shrink text. Row buttons: CTA 44, price digits 56, names 44, bar text 40.

## 2b. Padding gate (content never touches its parent)
- Every plate / button / text frame keeps >= 16 px (never < 12) from the inner panel edge on ALL sides, including info plates in a footer strip (a periwinkle level/income plate flush to the board edge was rejected). Place strip children with an explicit `STRIP_PAD`, and let the Play test assert `>= 12 px` for every child corner in the strip local space.

## 3. Centre on the LIT FACE, and prove it
- KT plate face = between the top outline (~16 px) and the bottom lip (~28 px). Content group rect: `offsetMin.y = lip`, `offsetMax.y = -top`; group height <= face height - 6 or it overflows and drifts (a 84 px group in an 80 px face gave dy = 3).
- **Add a PlayMode test** that spawns the popup (tutorial set DONE first), takes the union of the content children in the button's local space and asserts `|group centre - face centre| <= 2` and `resizeTextMaxSize >= 34` for every button (a PlayMode test that opens the popup with real data). Look at the 1920x1080 capture too; numbers never replace looking.
- Optical nudge: a glyph that sits low next to digits (gem) is lifted 4-5 px inside a wrapper slot that keeps its layout size.

## 4. Baked prefab + sprite traps
- Popups are baked prefabs (`BuildXInCode` is the source, one baker entry, runtime only spawns and fills data). Rebake after every builder change, then re-capture.
- **Frozen sprite copies:** runtime-resolved icons get persisted as `UiBaked/<name>_<rect>.png` on first bake. Replacing an icon means overwriting the source png AND that baked copy (same GUID updates every prefab), and verifying in a capture; a stale copy keeps showing the old art. `IconTrim.txt` may hold trim rects for the old art.
- Kit name aliases / Factory_Sprite groups can resolve a different file than the one you edited: print the resolved path from a script before blaming the cache.

- A project button-aspect guard (buttons <= 3:1) rejects very wide buttons: when you widen a popup, raise the button HEIGHT too (e.g. 330x114), do not just stretch width.
- Several editors in one Unity project: when a peer session edits the same popup, agree ownership by message (layout vs icon sweep), re-read the file before every edit, merge on top of the peer change (e.g. an info plate they added), never revert.

## 5. Process
- Tests set the tutorial DONE first, bottom 200 px free, buttons <= 3:1, `RequestScriptReload` after a Play session before EditMode, full EditMode before commit.
- `git add` with ONE missing path aborts the whole add; the commit then contains only earlier staged changes. Always check `git show --stat HEAD` after a commit.
- One agent owns the popup files; if a second session edits them, message it and split by ownership (icon sweep vs layout) before touching the same file.
