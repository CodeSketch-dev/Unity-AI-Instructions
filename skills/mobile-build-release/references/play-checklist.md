# Store release checklist (A = scriptable, H = human, A+H = agent prepares, human approves)

Nothing is uploaded or submitted without explicit approval for that action. Verify current numbers and policies in the consoles at release time.

## Google Play
| Step | Mode |
|---|---|
| Developer account, payments profile, 2-step verification; new personal accounts may need closed testing for a minimum tester count and period before production | H |
| Create the app (name, language, category, free/paid) | H |
| Opt in to Play App Signing; keep only an upload key (a lost upload key is resettable, a lost signing key is not) | H |
| AAB with increasing versionCode, current target API, ARM64 present, third-party native libraries 16 KB aligned | A (`unity-batch-build`) |
| Upload symbols zip and mapping file | A+H |
| Listing text (title, short, full description) in original naming (`clone-ip-safety`) drafted into `docs/store/listing.md` | A+H |
| Icon, feature graphic, phone screenshots (and tablet if supported); capture by script or `adb shell screencap`, art review by a person | A+H |
| Content rating questionnaire, data safety form (draft from the SDK inventory so it matches what SDKs really collect), ads and target-audience declarations | A+H / H |
| Privacy policy URL on a public page; consent flow (UMP) works before the first ad request; `app-ads.txt` when ads are used | A+H |
| In-app products created with ids matching the IAP catalog (`iap-catalog`); license testers added | H |
| Tracks: internal first, then closed, open, then staged production rollout; review the pre-launch report and Android vitals after rollout | H |

## App Store (needs macOS and Xcode; not available on a Windows-only machine)
Build the Xcode project in batch, sign with the team's provisioning outside the repo. Privacy manifest for SDKs and required-reason APIs, ATT usage text only if tracking, usage strings only for used capabilities, App Privacy labels, age rating, screenshots per required size, 1024 icon without alpha, TestFlight before release. Forms and review are human steps.

## Device checklist (human)
Low-end and modern device: cold start versus the budget, backgrounding and memory, FPS, heat after 10 minutes, ad and IAP test flows, consent flow, offline start, back button, safe area on notch devices. Use the `unity-qa-playtest` device checklist.

## Privacy policy template points
Data collected by ad and analytics SDKs, advertising ID, retention, contact email, children statement, deletion request path, third-party links. Placeholders for company and app name; host it on a static page.
