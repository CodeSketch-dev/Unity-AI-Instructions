# Shop page and item prefab trees (reference shop, soft numbers at 1920x1080)

```
Shop_Skin   (page script: _scrollRect, _itemPrefab, _imgThumbnail, button/text pairs)
 Root (inactive until its tab is selected)
  Board
   Content_BG   anchors (0,.5)-(1,.5), size (-825, 700)   bg panel sprite
    ScrollRect  stretch, inset 25 px, vertical
     Viewport (Mask) > Content: GridLayoutGroup cell 266x267, spacing 49x55, 3 columns, ContentSizeFitter vertical
     Scrollbar   vertical, 22 px wide
   Preview      anchors (1,.5), size 435x700, black sliced panel
    Thumbnail   stretch, inset 25/87, raycast off
    Button_{Unlock,Get,Equip,Equipped,IAP,IAP_Subscription}  347x116, anchors (.5,0), y 68.5, ONE active

Shop_Skin_Item  266x267
  components on the root: Image (alpha 0, hit) | Button | UIPressPrimeTween | AudioButtonSfx | Shop_Skin_Item
  Frame_Equipped, Frame_Unlocked, Frame_Locked
  Lock       black frame + lock icon top-right
  Notify     40x41 dot, top-right
  Thumbnail  inset 25 px
  Frame_Selected  284x285 (larger than the cell)
```
Behavior: click posts `Event_Shop_Skin_Item_Selected`; the page shows the preview and `UpdateAction()` activates exactly one action button; equip calls `config.Equip()` and an equip event refreshes every item frame. Ads: rewarded call then `config.Unlock()`; IAP: purchase facade with a callback.

Side-tab shop shell (full-screen page): header 1920x175 (back, title, nested currency bar) + SafeArea; tab column 285x740 of tab items (222x82: icon overhangs left 101x81, label, dot top-right 40x41, frame on/off sprites); content roots toggled by a tab-selected event. Full-bleed background is a sibling OUTSIDE SafeArea.
