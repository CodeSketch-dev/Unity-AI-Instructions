# Native overlay unit evidence

## Scope and acceptance

Keep the game's layout in screen pixels and adapt units once at the provider boundary. Preserve existing load, show, revenue and close behavior. A correction is accepted after conversion tests, platform compilation and a device measurement of the resulting native view; an Editor placeholder is insufficient.

Use the SDK's public sizing API when it matches its implementation. Prefer a narrow platform/version adapter over editing vendor code or adding a second ad provider. Reinspect the workaround after an SDK upgrade.

## Verified implementation: Google Mobile Ads Unity 11.6.0, Android

Inspection on 2026-11-03 of the installed `googlemobileads-unity.aar` with JDK `javap -c -p` showed:

- `com.google.unity.ads.nativead.UnityNativeTemplateAd$6.run` reads `AdSize.getHeight()` / `getWidth()` and assigns them directly to Android `FrameLayout.LayoutParams.height` / `width`, which use pixels.
- `UnityNativeTemplateAd.getLayoutParams` converts its horizontal and vertical offsets through `PluginUtils.convertDpToPixel` before assigning left/top margins.
- The installed managed API exposes `GoogleMobileAds.Api.MobileAds.Utils.GetDeviceScale()`, `NativeOverlayAd.GetTemplateWidthInPixels()` and `GetTemplateHeightInPixels()`.

For that implementation only, if the public wrapper stores all four values in dp: pass dimensions multiplied by SDK device scale to the custom-size renderer, retain offsets in dp, and let the plugin convert offsets. Do this under the Android player condition; Editor and iOS require their own inspected behavior.

Example: a 630 x 480 pixel slot at density 3 becomes 210 x 160 dp in pure layout. Passing those dimensions directly to the affected Android renderer produces 210 x 160 **pixels**. Its dimension adapter restores 630 x 480; x/y remain dp.

This is bytecode evidence, not proof of device output. A real Android layout measurement and screenshot remain required. Insets, dynamic resolution and template minimum constraints can still affect placement.

Primary references:

- [Native overlay API](https://developers.google.com/admob/unity/reference/class/google-mobile-ads/api/native-overlay-ad)
- [Device scale API](https://developers.google.com/admob/unity/reference/class/google-mobile-ads/api/mobile-ads/utils)
- [Version 11.6.0 managed Android client](https://github.com/googleads/googleads-mobile-unity/blob/v11.6.0/source/plugin/Assets/GoogleMobileAds/Platforms/Android/NativeOverlayAdClient.cs)

## Routing and behavior scenarios

- "Native is smaller than its calculated rectangle": read this skill, inspect SDK version/units, test fractional density, report actual device bounds or pending verification.
- "Add native to a loading screen": read this skill, measure a fixed slot, retain a no-fill path, close the overlay before scene activation.
- "Native covers the popup": read this skill, compute visible clipped content bounds, restore transforms on rejection/close, measure and screenshot the result.
- "Change rewarded-ad cash amount": this skill does not route on that request alone; use the rewarded/economy skills.

## Maintainer verification

Run `python -I tools/skillkit/skill_lint.py skills`; review the above positive/negative scenarios against the description and triggers. The scenarios are review cases, not an executed automated behavior eval. Publish through the instruction repository's normal combined publish flow after all concurrent skill changes are ready.
