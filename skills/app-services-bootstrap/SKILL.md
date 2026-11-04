---
name: app-services-bootstrap
description: "Use when a new or existing game needs the universal services every mobile game ships: internet gate, rating, ads gates, IAP, analytics, remote config, consent, settings, daily reward, haptics, localization, device policy, save, debug, lifecycle. Status table, install order, gaps."
triggers: services, cross cutting, bootstrap services, new project services, services checklist, internet check, rating, remote config, consent, gdpr, att, force update, crash reporting, local push, notification, lifecycle, dich vu chung, khoi tao du an, game moi, danh sach dich vu, kt style, knife tower style
---

# App services bootstrap

The checklist of cross-cutting services a mobile game needs. Use it at project start (install all) and as an audit on an existing project (fill the status column). It is a hub: each service has a leaf skill; this skill adds the status table, install order, exit criteria and the gaps.

## Principles
1. **Facade per service.** Gameplay code calls one static facade (`AdsHelper`, `LogHelper`, `IAPManager`, `LoadingScreen.Load`, toast push, localization `Get`). No SDK call outside the facade (grep to prove it).
2. **Services live in the persistent root prefab** (`persistent-root-prefab`) as scene-authored children, never `new GameObject` at runtime. Static-only services (facades, settings binder) are initialized from ONE `AfterSceneLoad` boot class.
3. **Framework first.** Before writing a service, check the installed SketchEngine package: `Internet` (popup + monitor), `Notification` (local push), `Settings` (`DataSettings`), `Modules/Appstore` (store review), `Modules/Taptic` (haptics), `Modules/Debug`, `Audio`, `Popup`. Use the installed API; check the package API first.
4. **SDK-agnostic.** Ads, analytics, remote config and consent sit behind interfaces (`ads-layer-generic`). A vendor can change; call sites must not.
5. **Safe with defaults.** Every remote value has a local default; the game must be correct offline on first launch.
6. **Tag every row** in your status table: `Reference` (the reference game ships it), `Studio addition` (our standard, the reference lacks it), `Optional module` (build only when the genre or store needs it).

## The service list (details: [services table](references/services-table.md))
| Group | Services |
|---|---|
| Boot | save warmup, persistent root, frame rate, device policy, settings binding, debug init |
| Money | ads facade + gates, IAP + restore, remote config, consent/ATT, banner |
| Player-facing | internet gate, rating, settings, daily reward, localization, toast, haptics, loading screen |
| Ops | analytics facade, lifecycle hooks, tutorial-done flag, debug menu |
| Studio additions | offline earnings (idle genres), real restore button, settings legal rows, real rating cooldown |
| Not in the reference (optional modules) | force update, crash reporting, local push, cloud save, server time, share ([absent-in-reference](references/absent-in-reference.md)) |

## Steps
1. Read the [install order](references/install-order.md); create the status table in the project docs (service, tag, location, leaf skill, status, evidence).
2. Install in order; each step has an exit criterion. Do not start ads before consent and remote defaults exist; do not start IAP before the catalog and receiver exist.
3. Wire cross-service gates once: the tutorial-done flag is read by rating, native ads and IAP entry popups; the ads-removed/VIP flag is read by the internet gate and the ads gates.
4. Add optional modules only when the genre or store needs them; log the decision.
5. Run the verification pass (below).

## Done check
- Status table complete, every row has evidence (file, screenshot, test) or an explicit "not applicable".
- Cold start from the boot scene AND from each scene opened alone: one root, one EventSystem, no missing facade.
- Airplane-mode run: internet popup, Try Again, ad calls fail safe, IAP does not grant.
- Remove-ads purchase hides the banner at once; VIP/ads-removed bypasses the internet gate.
- Language switch persists; settings persist; kill the app during a scene load and re-open (volume not stuck at 0).
- Ads and consent paths tested on a real device, not only the Editor mock ([ads gate matrix](../ads-layer-generic/references/ads-gate-matrix.md)).

## Pitfalls
- The same service twice: a vendor SDK popup AND a game popup (two no-internet popups). Disable one.
- A service that lives in the boot scene only: scenes opened alone then lack it. Place the root in every playable scene (duplicates destroy themselves).
- Date logic on the device clock is spoofable; decide whether rewards need server time.
- SDK keys in code or in a skill: keys live in ignored per-app config assets, never copied between projects.

Leaf skills: `ads-layer-generic`, `ads-popup-flow`, `iap-catalog`, `unity-iap-port`, `internet-gate-popup`, `rating-prompt-flow`, `settings-pause-offline`, `localization-pipeline`, `device-tier-policy`, `save-and-crash-safety`, `data-persistence-facts`, `debug-cheats-menu`, `analytics-events-taxonomy`, `recipe-retention-timers`, `scene-flow-loading`, `boot-sequence-setup`, `tutorial-phase-system`.
