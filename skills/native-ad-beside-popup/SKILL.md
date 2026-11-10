---
name: native-ad-beside-popup
description: "Fit native ads beside popups and inside fixed loading slots. Use when adding native half/rect ads or debugging wrong native size, empty gaps, or covered content."
triggers: native ad, native half, native rect, native size, admob native, native loading, sai kich thuoc native, quang cao native, native che popup
---

# Native ad beside a popup

- Ask the provider synchronously `IsReady`. Not ready: show nothing, shift nothing.
- Compute a PURE layout first (unit-tested): free space -> ad width, shift only as much as needed, keep clear of banner strip and HUD, close button anchor >= 88 px inside the ad rect.
- Order: ready-check -> layout -> slide popup -> show ad. Never shift an already open popup late.
- Attach timeout (~1.5 s), a rejected show or an expired ad: slide the popup back.
- The ad can outlive the popup: it owns a delayed close; close it on scene switch, app pause, ads removed, and when any popup it could cover opens.
- Providers that cannot take a pixel rect expose a fixed rect through the same layout call.
- Ship behind a kill switch (off by default) and a fake provider that simulates ready / not ready / late / expire / fail; test each.
- After a full-screen interstitial, decide native full vs armed half with one pure function (ads removed, config, ready).
- Verify on a device: Editor has no fill.
- The native must never cover popup content: when the popup is too wide to shift aside, scale the popup uniformly (about 0.6-1.0, prefer >= 0.8) so it fits fully beside the ad; if it still does not fit, show no native and keep the popup centred. Do not fall back to drawing the ad over the popup.
- Measure the popup content rect from visible graphics only: clip each graphic to its parent Mask/RectMask2D/ScrollRect viewport, otherwise a long scroll list reports a huge rect and every popup is classed "too big". Restore position/scale/pivot exactly when the ad closes or the popup is disabled.

## Pixel/point/dp boundary (before changing sizing)

1. Inspect the installed SDK version and platform implementation. Record the units of width, height, x and y separately; do not infer all four from one parameter or another SDK's wrapper.
2. Measure the slot in screen pixels using its canvas camera; convert bottom-left Unity Y to top-left native Y as `screenHeight - rect.yMax`. Apply display safe-area insets exactly once.
3. Convert pixels to logical dp/points with the ads SDK's device-scale API. Never use `Screen.dpi / 160`: physical DPI can differ from Android's configured logical density.
4. Check custom-template implementation when the rendered size differs. Google Mobile Ads Unity **11.6.0 Android** has a verified mixed-unit path: custom template dimensions reach pixel layout parameters directly, while offsets are converted from dp. Compensate at the provider boundary only; do not apply that workaround to iOS, Editor, other formats or uninspected SDK versions. See [native unit evidence](references/native-units.md).
5. Test conversion with density 1, 2, 2.625 and 3; assert recovered pixel bounds and the Y flip. Also test native unavailable/rejected: the loading flow still completes and leaves no empty shifted popup.
6. On Android, use test ads, wait for native layout, compare actual SDK view dimensions with the requested pixel slot, and inspect a device screenshot for clipping, overlap and close-button accessibility. Record requested/actual dimensions, SDK version and density. Editor screenshots and formula tests cannot prove native overlay sizing; report device validation as pending until measured.

- Editor fake overlay on the Game View: map game pixels into the GAME IMAGE rect (GameView internal viewInWindow + targetInView / pixelsPerPoint), never the whole window (toolbar, scale slider, letterbox margins shift and enlarge it). Check it by eye in the Game View: game-view screenshots do not include Editor overlays.
- An Editor overlay element (IMGUIContainer on the Game View root) must be sized to its own rect: a full-window element with pickingMode Position eats every click, so game buttons (popup close) look dead.
