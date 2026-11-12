---
name: ui-page-item-prefab
description: "Use when building a popup, shop, daily or list page from prefabs: page script on the prefab root, typed item prefab filled into a ScrollRect, reuse of authored children, item Init(config), press and sfx components, subscribe and cancel lifecycle, per-feature prefab folders."
triggers: page, popup page, list page, item prefab, scrollrect items, shop page, daily login, tab page, page item, field naming, popup system, trang popup, danh sach, o vat pham, trang shop, kt style, knife tower
---

# UI page + item prefab (structure and behavior)

Boundary: this skill owns STRUCTURE and LIFECYCLE. Look, spacing and measuring stay in the `ui-always` set (`ui-popup-anatomy`, `ui-scroll-board`, `ui-tabs`, `ui-button-anatomy`, `ui-center-alignment`); states and patterns in `ui-pattern-library`. UI is authored in Edit Mode inside the prefab (`ui-edit-mode-authoring`); code only fills data and toggles states. Read `ui-always` first for any UI task.

## 1. Page prefab
- The page script sits on the prefab ROOT, next to `Popup` + `CanvasGroup` (popups) or the page root component. Tree: `Feature_Popup > Root > Board > {Title, Btn_Close, Content (ScrollRect > Viewport > Content), action Btn_*}`. Full trees: `references/shop-skin-tree.md`, `references/daily-popup-tree.md`.
- Serialized dependencies are authored in the prefab: `[SerializeField] ScrollRect _scrollRect; [SerializeField] Feature_Item _itemPrefab;` (typed reference to the item prefab component, not `GameObject`), plus role-prefixed fields: `_btnX`, `_txtX`, `_imgX`, `_goX`, `_frameX`.
- Prefab folders mirror features: `Prefabs/<Feature>/` (`Shop/{All,Boost,Skin,Sound,Trail}`, `Daily`, `Currency/...`); only generic buttons/HUD pieces live in `Prefabs/UI/`. Names `Feature_Popup`, `Feature_Item`.
- One page prefab per feature per minigame (`minigame-consistency-contract`): do not nest or variant another minigame's page.

## 2. Filling the list
1. Reuse authored children first; instantiate only when they run out: `var item = i < existing.Length ? existing[i] : Instantiate(_itemPrefab, _scrollRect.content);`
2. Hand data in with `item.Initialize(this, config, i)` / `Init(config)`; the item never looks data up itself.
3. Keep `readonly List<Feature_Item> _items = new(32)`; refill on `OnEnable`, never build items with `new GameObject`.
4. Pooling is not needed for fixed-size shop/daily lists (instantiate once); long dynamic lists use a pool (`pool-everything`).
5. Show the right action button from item state: exactly one of several (`Unlock/Get/Equip/Equipped/IAP`) is active.

## 3. Item prefab anatomy
- Root = the Button: `Image` (alpha 0 hit area for icon buttons, raycast on) + `Button` (Transition None) + `UIPressPrimeTween` (0.9 / 0.1 s) + `AudioButtonSfx` + `<Feature>_Item` script. Exactly one of each; audit with `Qa_PressAnim`.
- Derive from the framework button base (`UIButtonBase`: finds the Button, wires `Button_OnClick` in `Awake`) when the item only needs a click.
- Children by role: `Frame_Selected/Locked/Unlocked/Equipped`, `Thumbnail`, `Lock/Icon`, `Notify` (dot, `ui-notification-dots`), `Btn_*`, `Text_*`. State = child GameObjects toggled with `SetActive`, not one image with many conditions.
- Text: localize component on static labels, shrinking autosize (`ui-text-autofit-system`), outline from the shared material set.
- Selected state is visible without colour alone (larger frame).

## 4. Lifecycle
| Owner | Subscribe | Unsubscribe / cancel |
|---|---|---|
| Item | `Awake` (bus, `OnValueChanged`) | `OnDestroy` |
| Page | `OnEnable` refresh + active-only listeners | `OnDisable`; cancel `CancelToken`, stop tweens in `OnDisable/OnDestroy` |
| Focus/scroll helper | UniTask + `CancelToken` | cancel before replace |
Item click posts a bus event (`Event_Shop_Skin_Item_Selected`) or calls the page; the page updates preview and action buttons.

## 5. Popup system use
- Spawn popups ONLY through `PopupManager.Create(prefab)` (from a `PopupButtonOpen` with a serialized prefab, a factory static `Show()`, or an event). They are destroyed on close, never pooled or SetActive-toggled; guard single-instance popups with a `HasInstance` check.
- Back/Escape closes the top popup only; no per-screen back handlers. Close buttons wire `Popup.Close` (persistent UnityEvent). Popups play no open/close sfx; sound comes from button components.
- `Close()` is ignored while the open sequence plays: owners must not consume state before the close succeeded.
- Hide the HUD while popups are open via `PopupManager.EventPopupOpened/Closed`.

## 6. Numbers (from the reference shop, soft defaults)
Shop item 266x267 (grid 3 columns, spacing 49x55); preview panel 435x700; action buttons 347x116 anchored bottom-centre; scroll inset 25 px; tab 222x82; page header 175 high; daily card 431x617; press scale 0.9 / 0.1 s. More in `references/numbers.md`.

## 7. Done check
- Page and item prefabs saved in Edit Mode, 0 missing references, `_itemPrefab` typed and assigned.
- Item prefab has exactly 1 press + 1 sfx component.
- Open from its real entry in Play, scroll, select, close: Console empty; subscribe/unsubscribe balanced.
- UI gate: layout audit totals, dx/dy measured, Play screenshot looked at.

## Pitfalls
- Generic `GameObject _itemPrefab` forces `GetComponent` per item.
- Subscribing items in `OnEnable` while the page recreates them: leaks.
- Debug `Update` input in a page outside `#if UNITY_EDITOR`.
- Rebuilding all items on every data event instead of refreshing states.
