---
name: native-ad-beside-popup
description: "Show a native ad next to a popup without gaps or covered content: ready-check first, pure layout, slide the popup, then show. Use when adding side/half native ads to popups or debugging an empty gap or an overlapped HUD."
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
