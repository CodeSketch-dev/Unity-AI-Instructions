---
name: ui-tabs
description: "Tab strip and content panels switched by a StaticBus tab-selected event with on/off frames and notify dots. Use for side-tab shops, inventory categories and settings sections. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# UI tabs

Reference: knife-tower `Shop_All_Tab`, `Shop_All_Content` (report 07, VERIFIED).

1. A tab button posts `StaticBus<Event_X_TabSelected>(type)`; every tab and every content panel listens (`static-bus-events`: subscribe in `Awake`, unsubscribe in `OnDestroy`).
2. Each tab swaps its `Button.image.sprite` between `_frameOn` and `_frameOff` (no tint, no tween); content panels toggle SetActive. Default tab selected explicitly on open.
3. Side-tab shop: left ScrollRect strip ~285 wide, tab ~222x82 (icon left ~101x81, label, notify dot top-right), content panels stacked (Speed, Trails, Offers...). Dot via a data event (`ui-button-anatomy`).
4. Panels may defer heavy content until first shown; sort sold-out/owned last.
5. Tabs are buttons: press feedback and sfx apply; selected state must be visible without colour alone.

Layout and scroll of the content: `ui-scroll-board`; patterns: `ui-pattern-library`.
