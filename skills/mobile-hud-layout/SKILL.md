---
name: mobile-hud-layout
description: Single source for mobile HUD zone map and sizes (joystick, action cluster, rails, safe area, thumb reach, touch targets, popups). Use when placing or changing any HUD element or on overlap/unreachable-button reports.
---

# Mobile HUD layout

The HUD is a small number of fixed zones. Putting each element in its conventional zone makes the game feel familiar to Roblox players and prevents overlap. Zone coordinates and sizes live in `references/layout-zones.md`; read it when placing or sizing elements. `assets/SafeAreaFitter.cs` is a ready component for the safe-area root.

## Zone map (defaults; the reference game wins when it differs)
```
 TOP-LEFT        TOP-CENTER          TOP-RIGHT
 settings        level/zone/progress  currency (coins, gems) +
 left rail ->    objective/timer      right rail <- (shop, pet, backpack, daily)
 (daily reward,                       
  events, offers)  [world view: keep clear]   
 BOTTOM-LEFT      BOTTOM-CENTER       BOTTOM-RIGHT
 joystick         hotbar/tools        action cluster: primary (attack / pick up / drop),
 (floating)       (compact)           jump, 1-3 secondary skills in an arc
```
- **Joystick**: bottom-left, floating (appears where the thumb lands in the left ~45% of the screen, lower ~60% height). Never place buttons there.
- **Action cluster**: bottom-right. The primary action is the largest button; contextual actions (Attack, Pick up, Drop, Interact) **share one slot** and swap by state instead of stacking. Jump sits above-left of the primary in the thumb arc.
- **Settings**: top-left (gear). Keep it small; frequent actions must not live in far corners.
- **Level/progress**: top-center. Zone-entered banners slide in from the top-center and fade.
- **Feature buttons** (daily reward, pet, backpack, shop, quests, events): vertical or short horizontal rails under the top-left and top-right corners, 3-5 items per rail, most important nearest the corner. Badge (red dot/number) for pending items.
- **Currency**: top-right (or top-center under progress if the reference does so), with a "+" shortcut to the shop.
- **Bottom-center**: hotbar/tool slots, above the OS gesture area.
- **World view center**: keep clear. Toasts (rewards, join/leave) in the upper-middle; floating numbers in the world, not on the HUD.

## Rules
1. **Safe area**: parent all HUD under a SafeArea root (`assets/SafeAreaFitter.cs`); decorative backgrounds may extend full-bleed.
2. **Canvas Scaler**: Scale With Screen Size; reference 1080x1920 (portrait) or 1920x1080 (landscape); pick Match by orientation per the reference and verify at the three test ratios.
3. **Touch targets**: >= ~120 px at the 1080 reference width (~48 dp); primary action 180-240 px; gaps >= 24 px between neighbors. Give small icons a larger invisible hit area.
4. **Thumb reach**: frequent actions in the lower third; rarely used in top corners.
5. **No overlap**: after building, list every interactive rect and verify no pair intersects, including the *largest* state of swapping buttons and the notification banner.
6. **Multi-touch**: joystick, camera drag and buttons work at the same time (see `mobile-input-controls`); UI must not swallow the camera-drag area.
7. **Progressive disclosure**: during the FTUE show only the joystick and the primary action; reveal feature buttons as they unlock (matches Roblox flow and reduces clutter).
8. **State clarity**: disabled/locked states greyed with a lock; cooldown radial fill; pressed scale ~0.92-0.95.
9. **Popups**: centered panel, dimmed backdrop that blocks input, close "X" top-right of the panel, scale-in ~0.2 s with ease-out-back, one popup at a time via the project's popup manager.
10. **Asset hygiene**: 9-slice sprites with borders set; atlas per screen group; Raycast Target off on decoration; separate canvases for static vs frequently changing elements.

## Verification (always)
Capture the Game view at 9:16, 9:20 (tall notch phone) and 3:4 (tablet), plus landscape if supported. Check: safe area respected, no overlap, nothing cut off, targets reachable. Attach screenshots to the report. Then continue with `ui-clone` for fidelity against the reference.
