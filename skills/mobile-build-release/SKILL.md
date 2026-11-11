---
name: mobile-build-release
description: "Build and release checks for Android (APK/AAB) and iOS: versioning, signing safety, size, permissions, store checklist. Use when building, testing on device, uploading to stores, or a build fails/is too large."
---

# Mobile build and release

Builds and uploads are outward-facing and hard to undo. Do not start a store submission or upload without explicit approval for that action; preparing and verifying is always fine.

## Pre-build checklist
1. Console clean; `done-means-wired` and `unity-qa-playtest` gate passed for the target milestone.
2. Versioning: semantic `bundle version`, monotonically increasing Android `versionCode` / iOS build number; set from one place.
3. Scripting backend IL2CPP, ARM64 (Android) and per-platform stripping tested (check `link.xml` for reflection-used types).
4. Development build flags only for test builds; release builds without profiler/cheats (guard with defines).
5. Scenes in build settings, correct order; Boot scene first.
6. Quality tiers and graphics API as set in `unity-project-bootstrap`.
7. Permissions: only what is used; ad/analytics SDK manifests reviewed for extra permissions.

## Android
- Debug: APK for device tests. Release: AAB for Google Play.
- Signing: keystore and passwords are secrets. Never put them in the repo, logs or chat; configure them through the local environment or ignored local settings. If missing, ask the human to provide the keystore locally.
- Check target API against the current Google Play requirement and any 64-bit/16 KB page-size requirements for the engine/plugins version (verify the latest policy rather than relying on memory).
- Shrinking: R8/minify with keep rules for the SDKs used.
- Size: report AAB size; investigate largest assets via the build report; compress textures (ASTC), audio (Vorbis/AAC, streaming for music), strip unused shaders and mesh data.

## iOS
- Build to Xcode project; signing via the team's provisioning, set in Xcode or local batch runner; do not store certificates in the repo.
- Required usage strings and privacy manifest entries for the SDKs used; ATT prompt text if tracking is used.
- Metal only; check frame rate caps and safe area on notch devices.

## Post-build verification
Install on at least one low-end and one modern device (human), run `unity-qa-playtest` device checklist: cold start time, memory (does it survive backgrounding), FPS, heat after 10 minutes, ad/IAP test flows in test mode.

## Store readiness (hand to the human)
Icons, screenshots, short/long description (original naming per `clone-ip-safety`), content rating, privacy policy URL, data safety form, target audience/ads declarations (`monetization-integration`), testing track first.

## Automation and checklists
Local headless builds and size gates: `unity-batch-build`. Full store checklist with the scriptable versus human split, Play App Signing, tracks and privacy points: `references/play-checklist.md`.

## Report
Build output path, size, version numbers, settings changed, what was verified vs not, and the exact manual steps left for the human.

## Changed C# default does not reach the build (serialized value wins)
- A `[SerializeField] string _address = "x"` default only applies to NEW components. If a prefab/scene already imported with the old default, the player takes the value cached in the Library import artifact, not your new initializer. A "domain/IP" APK built by editing only the C# default kept the old LAN IP and could never connect over 4G.
- Verify before shipping: unzip the APK and `grep -a` the new value in `assets/bin/Data/*` (the serialized level data), not only in `global-metadata.dat` (that only holds the C# literal).
- Fix: write the field into the prefab/scene (or set it through SerializedObject in the build script), rebuild, re-grep; restore the temporary edit afterwards.
- Put the connect address on the phone debug overlay (addr / transport state / attempts) so one screenshot shows what the build really uses.

## Release hygiene: debug overlays
- SRDebugger (SketchEngine plugin) auto-initialises in every build; its Settings.asset `_triggerEnableMode` must be 3 (DevelopmentBuildsOnly) or the debug tap trigger ships to players. Grep for the Settings asset before any release build.
- Unity MCP: long bake menus in one script-execute call time out ("after 10 retries") and can restart the Editor; run 2-4 bake menu items per call and confirm each returns True.
