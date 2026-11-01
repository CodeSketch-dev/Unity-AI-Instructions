---
name: ui-notification-dots
description: "Default red notification dots on HUD buttons, tabs and cards when the player can afford an upgrade or claim something. Use at game start and when building any shop, upgrade, collection or reward screen. Part of the ui-always set."
---

# Notification dots (default feature)

Not optional and never asked for: every game gets red dots. Add them while building the feature, say in one line what you added, and do not ask permission.

## 1. At project start (once)
Create three small pieces, in the shared UI folder of the game (for example `Logic/Notify/`):
- **Dot helper**: `Attach(Transform host)` builds a red disc with a white ring at runtime (generated sprite, cached, reset in a `SubsystemRegistration` hook), top-right of the host, ~34 px, inset about (-8,-8). Idempotent per host (find child `NotifyDot` first), `raycastTarget` off, `LayoutElement.ignoreLayout = true`, last sibling, starts inactive. `Set(GameObject dot, bool visible)` toggles only when the state changes. Runtime creation means prefabs and builders need no edits.
- **Pure rule**: `ShouldNotify(bool owned, bool moneyBuyable, bool affordable, int index, int bestOwnedIndex) => !owned && moneyBuyable && affordable && index > bestOwnedIndex`. Cover it with an EditMode test (qualifies, cosmetic, lower tier, owned, unaffordable).
- **Query class** per game (`Notify_<Game>`): best owned index per item family, `IsItem(...)`, `AnyInShop(...)`. It reads data, never UI.
Add a line to the project checklist so later features follow the same steps. Related: `ui-button-anatomy` (dot size and anchor), `ui-tabs`.

## 2. When a dot is shown
All must be true:
- The item raises a stat or progression (power, speed, income, capacity, level, unlock), or is a reward that can be claimed right now (daily, free gift, finished quest, unclaimed collection entry).
- Purchases: not owned, strictly better than the best owned one of its family, sold for the soft currency, affordable now.

## 3. When NOT
Skins, decorations, cosmetics, bundles, IAP-only or ad-only items, owned or lower-tier items, anything that changes no stat. Respect a product decision that a place has no marker. Never show a count; the dot is on or off.

## 4. Where (every level that applies)
1. The HUD or menu button that opens the screen (lit when anything inside qualifies).
2. The tab button inside the screen, only for tabs that sell qualifying items.
3. The item or card itself (pass a `notify` flag into the card's refresh method).

## 5. Wiring
- Create dots in `Awake`; recompute in one `RefreshNotify()` method.
- Recompute on each input that changes the answer: currency changed, ownership changed, equipped or level changed, popup opened, cooldown finished.
- Subscribe and unsubscribe symmetrically (`OnEnable`/`OnDisable`, or open/close plus `OnDestroy`). No per-frame polling when events exist.
- Embedded or reused popups: attach tab dots when first opened, not in the constructor.

## 6. Verify
Refresh and compile, Console clean, run the rule test, then in Play Mode give money and check HUD button, tab and card light up, and that a skin tab stays dark. Report what you could not see.
