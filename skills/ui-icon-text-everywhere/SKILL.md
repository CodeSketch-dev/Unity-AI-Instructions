---
name: ui-icon-text-everywhere
description: "Every toast, currency value, reward or status text is an ICON on the left plus TextMeshPro on the right (UI in a HorizontalLayoutGroup, world text with a TMP sprite tag). Use when adding or touching any toast, popup number, floating value, currency label, notice lane or overhead text."
triggers: toast, notification, notice, cash, currency, reward text, floating text, popup number, overhead label, tmp sprite, sprite asset, icon left, thong bao, tien, so tien, bieu tuong
---

# Icon left + TextMeshPro right, everywhere

Standing owner rule: no bare text for anything that carries meaning. A value always reads `[icon] value`, icon first (left), text second (right).

| Surface | Build | Notes |
|---|---|---|
| UI toast / notice lane / popup / HUD chip / reward line | `Row` (HorizontalLayoutGroup, MiddleCenter, control child width ON) -> `Icon` (Image, preserveAspect, <= ~50% of row height) + `Label` (**TextMeshProUGUI**) | one prefab or one builder helper for ALL toasts; never hand-place the icon |
| 3D / world-space value (floating "+5M", income over pets/eggs, board numbers) | ONE **TextMeshPro** (3D) object whose string starts with a sprite tag: `<sprite name="cash"> +5M` | icon comes from a **TMP Sprite Asset** (assigned on the TMP component or as default), NOT a second quad/renderer. Keeps one draw, one pool entry |
| Damage / pickup numbers over blocks | same as 3D text; pooled; never `Instantiate` per hit | |

Rules
- Currency icon = the game's cash/gem icon from the shared icon family; amounts use the shortened bare-number format (no `$`).
- Colour: white or bright saturated gold/green/cyan with a thick black outline; the plate behind is mid-tone, never near-black; text is never drawn behind a plate (check sibling order) and never dark.
- Toasts are timed: hold ~2.5 s then fade ~0.4 s and hide (unscaled time). No toast may linger or stack; clamp the lifetime in code.
- Sprite tags: build/maintain ONE TMP Sprite Asset per icon family (cash, gem, power, egg, star...) from the icon atlas; reference icons by `name`, keep names stable, add the asset as fallback of the font asset so every TMP can resolve it. Tint with `<sprite name="x" color=#FFFFFF>` only if the sprite must change colour. Align with `<voffset=-0.1em>` / `<size=110%>` instead of nudging transforms.
- Build once in a shared helper (e.g. `Ui.IconText(parent, iconSprite, text)` / `WorldText.Value(icon, text)`); every new toast goes through it.

Verification (do it, do not ask the user)
1. Script: for each toast/value prefab assert `Icon` sibling index < `Label`, both inside the row rect, label is `TMP_Text`, no legacy `Text`.
2. Play: trigger each toast, screenshot WITH post-processing, confirm legible colour, correct order (icon left), and that it fades away.
3. Add/extend an EditMode test for the pure parts (lifetime clamp, string builders that prepend the sprite tag).

Related: `ui-icon-label-layout` (buttons), `ui-text-tmp`, `ui-text-autofit-system`, `world-label-recipes`, `ui-feedback-toasts`, `ui-always`.

## Icon must match the meaning; missing icon = generate it, never reuse a wrong one (owner rule)
- A stat / currency / counter shows the icon of WHAT it is (throw power = muscle arm, speed = shoe, cash = cash, luck = clover). Reusing another stat's icon (speed shoe for throw power) is a defect.
- No fitting icon in the project or sibling games: generate it with `generate_game_image` (codex-game-art) in the style of the game's existing icons (chunky outline, same palette), save under `Assets/_Art/2D/GUI/<Game>/`, import as Sprite, put it in the prefab AND its builder (idempotent). The MCP call may report a timeout while the file still arrives: check the file with a bounded wait, then use it; if it never appears, draw it yourself, never ship the wrong icon.
- Text-only counters are defects: every number that has a meaning gets icon + text in one centred HorizontalLayoutGroup.
- Native half ad / popups: only the POPUP scales or shifts; HUD bars and buttons never move (NativeHalf_HudAvoid is a no-op by owner rule).
- World labels above pets (name, income, rarity) are never hidden, also while carried or revealed.
