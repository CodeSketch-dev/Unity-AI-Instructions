# 20 - Retention, meta systems, analytics, localization (complete-game checklist)

Scope: every meta system a Roblox-clone mobile game ships, for LOCAL-ONLY games (no server). Sources read read-only. Tags: **V** = VERIFIED (file read, cited), **I** = INFERRED / proposed standard. Roots (relative `Assets/`): KT = `knife-tower/knife-tower-troll-unity` (really a Speed Keyboard game), ME = `monkey-escape/monkey-escape-unity`, TBE = `thunder-break-egg/break-and-steal-unity`, SAE = `steal-an-egg` (`_ROOT/Scripts`), PB = `problox` (`4_Game_HungryWorm`), RAP = `ride-a-pet`, TRW = `Tiny Relax World`. `docs/pipeline-catalog/05, 07, 08` already cover ads gating, IAP, daily login, jackpot, popups; this file does not repeat their tables, it links them and fills the rest.

## 0. Coverage matrix (what actually exists)

| System | KT | ME | TBE | SAE | PB / RAP / TRW | Verdict |
|---|---|---|---|---|---|---|
| Ads wrapper `AdsHelper` | V | V | V | V | PB/RAP: Bounce SDK files present (I: same wrapper) | Standard exists, needs provider-agnostic split |
| IAP + restore | V | V | V (`Data_IAP`, `Logic/IAP`) | V | - | Standard exists (doc 05 sec 4) |
| Daily login | V 30-day | V 30-day | not found | not found | PB V 7-day (`DailyReward/*`) | Two designs; see 3 |
| Spin wheel | slot machine only (`Jackpot_*`) | same | no | no | PB `ResultSpinBar` only | **Wheel absent**; slot is the nearest |
| Quests / achievements / badges | no (only tutorial pointers `Quest_*`) | no | no | no | RAP: `MMAchievement*` is Feel plugin, unused (I) ; `PanelRanking` has an "Achievements" tab (UI shell) | **GAP** |
| Codes / redeem | not found | not found | not found | not found | not found | **GAP** |
| Rating prompt | V (`RatingHelper`, 2 triggers) | V | no | no | Bounce `PopupRating` star popup (all Bounce projects) | Standard exists |
| Settings | V music/sound/vibration + language | V | V `Game_Settings`, `Settings_Popup` | PanelSetting (RAP) | RAP `PanelSetting` | Quality + privacy rows **GAP** |
| Pause | not found (doc 07 sec 5 confirms) | not found | not found | not found | not found | **GAP** |
| Offline earnings | no | no | no | V `OfflineEarningPopup` + `PetIncomeManager` | - | One reference |
| Local notifications | framework only, unused by game | same | framework (SketchEngine `Notification/`) | no | - | **GAP in games** |
| Analytics taxonomy | partial (`LogHelper`) | partial | no | V funnel (`LogHelper`, `UserDropTracker`) | - | Needs taxonomy file |
| Remote config | V (`RemoteConfig`) | V | V (`RemoteConfig.Dev`) | V | - | Standard exists, local-only caveat |
| Localization | V 9 locales | V | not found (grep: no Localization usage in TBE scripts) | no | - | Standard exists in KT/ME |
| Tutorial / FTUE | V phases | V `Data_Tutorial` | V `Tutorial_*` (4 phases) | V `Tutorial*` | KT-clone in PB `_Thunder` | Standard exists |
| Loading / splash | V (Bounce Splash + `LoadingScreen`) | V | V `Logic/Loading` | - | - | Standard exists |
| Leaderboard + bots | SDK message classes only, no UI | same | no | no | RAP V fake ranking (1000 names) | Fake-local standard from RAP |
| Friends / invite / share | no | no | no | no | no | **GAP** (substitutes in 16) |
| Force update | partial (`upAppVersion`) | partial | partial | partial | - | **GAP** (no store-version check) |
| Crash / ANR handling | no | no | no | no | no | **GAP** |
| Save corruption recovery | atomic write only | same | same framework | MemoryPack | - | **GAP** (see 18) |

## 1. Ads layer: provider-agnostic `AdsHelper` (the shared mechanism)

**What projects do (V).** Game code only calls the static `AdsHelper`; it wraps `BounceAdsSdk` which selects `AdsMAX` / `AdsAdmob` / `AdsIronSource` by define (`USE_MAX`, `ADMOB`) (KT `Logic/Ads/AdsHelper.cs`, `BounceSdk/BounceSdk/Ads/*`; doc 05 sec 5, doc 08 sec 5.2). Each app has its own keys in `Resources/BounceSdk/Bounce.BounceConfig.asset`; the setup is identical. Formats: rewarded, interstitial, banner (+ collapsible banner, MREC), app open (`BounceAppOpenManager`), native (`MaxNativeAds`, ME `Monetize_AdsNativeManager`). SAE variant (V `_ROOT/Scripts/Ads/AdsHelper.cs`): placements are a 17-value int enum (101-109 gameplay, 201-207 popup), `placement.ToString().ToLower()` is the logged id; interstitials blocked until `DataTutorial.Tut1Done && Tut2Done` (no ads in FTUE); "break ads" = 3-2-1 countdown "Break Ads in {i}s" only when the player is in a safe zone, cancelled if they leave; rewarded in Editor/DEVELOPMENT_BUILD returns true when `DataAds.RewardEnable` is off (`DataAds` is a debug toggle block); every ad show marks `UserDropTracker` (see 11).
Gating defaults (V `RemoteConfig.cs`): inter start 60 s, between 40 s, per-placement `{timeStartShow 60, timeBetween 30, sessionToShow 1, enable, adsBreakEnable}`, banner/app-open/native start 60 s, collapsible gap 30 s, `upAppVersion=-1` (suppresses ads on the version flagged "newest", a store-review safety switch).

**Standard solution (I) - split the stack in 3 layers, same for every app:**
1. `IAdsProvider` (per SDK adapter): `Init(consent)`, `Load/Show(format, placementId)`, `IsReady(format)`, events `OnShown/OnClosed/OnRewarded/OnFailed/OnPaid(revenue)`. Adapters: `AdsProvider_Max`, `AdsProvider_Admob`, `AdsProvider_Fake`.
2. `AdsPolicy` (pure C#, unit-testable): remove-ads flags, cooldowns, session/level gates, per-placement config. Inputs: `AdsConfig` SO (local defaults) overlaid by remote config; no provider types.
3. `AdsHelper` static facade (the only API gameplay may call): `ShowRewarded(AdsPlacement, Action<bool>)`, `ShowInterstitial(AdsPlacement, Action onClosed)`, `ShowBanner/HideBanner`, `IsRewardReady`, `IsInterstitialOkToShow`, `IsAdsRemoved`, `ShowAppOpen`. Keys are NOT in code: per-app `AdsKeys` asset in an ignored folder (doc 08 anti-pattern: keys tracked in git).

Rules (V where noted): rewarded callback is always invoked exactly once, `false` + localized "No ads available" toast when not ready (KT); VIP/remove-ads removes banner+inter but NOT rewarded (V KT, doc 05 sec 5.1); placement = stable int enum, logged by name; interstitial only at natural breaks (death, revive cancel, checkpoint, popup close, result), never during FTUE (V SAE); never an inter on top of a rewarded; ad-free grace after IAP purchase (I, 120 s); app-open only from the 2nd session and never on the first foreground after an ad (I, store policy; `showAppOpenFirst=false` V default).

**Cooldown table (starter defaults, V numbers from KT code, adjust per app):** inter first 60 s of install, 40 s between; rewarded no cooldown; banner always on in gameplay when not removed; app open 60 s after install and >= 4 h between (I); NoAds popup after 3 completed inters, once per session (V ME/KT `AdsBreak_Static`).

**Editor fake ads (I, closes gap):** `AdsProvider_Fake` shows a full-screen test overlay (5 s countdown, Close/Reward buttons, "simulate no-fill" toggle, "simulate fail" toggle). Current behavior (V) is "Editor returns true instantly", which hides the no-fill/closed-early paths. Debug menu rows (`debug-cheats-menu`): skip-ad, force no-fill, remove-ads toggle, print ad log.

**Consent (V/I).** Delegated to MAX Consent Flow (`consentFlowEnabled`, GDPR alert, localized ATT; V `AppLovinInternalSettings.json`, doc 08). First launch shows `PopupPrivacy` before `BounceSdk.InitOnStartup` (V). Standard: `IConsentService` with states `Unknown/Granted/Denied/NotRequired`, `AdsPolicy` passes `limitedAds=true` when denied. If audience includes kids, provider choice and ad settings change (human decision; see `monetization-integration`).

**GDD must specify:** every placement (id, screen, trigger, reward amount/multiplier, shown-if conditions, fallback when no ad), inter cooldown/session/level gates, remove-ads scope (what it removes), VIP interaction, FTUE ad-free boundary, app-open/native/banner positions and banner clearance, kids/consent stance.

## 2. IAP catalog + restore (summary; details in doc 05 sec 4)

V: Unity IAP 5.4.1, JSON `Resources/IAPProductCatalog.json` (base id + `.update`/`.stand` variants), `IAP_Product_Receiver` subtype switch, `TryMarkTransactionProcessed`, entitlement-based restore (`CheckEntitlement`; `IAP_Button_RestorePurchased` is a cosmetic 3 s spinner = compliance gap), store price text with "N/A" fallback. Price ladder 0.99/2.99/3.99/4.99/9.99/19.99/49.99/69.99/99.99.
Data model (I, pairs with `Data_IAP` V): `Dictionary<baseId,int> purchases`, `totalPurchaseCount`, `firstPurchaseUtc`, `processedTransactionIds` (bounded list). UI: shop tabs, starter pack popup, remove-ads popup, VIP popup, restore button (Settings + Shop; hidden on Android if policy allows, mandatory on iOS), price-loading state. Events: `iap_open`, `iap_click`, `iap_success`, `iap_fail`, `iap_restore` (see 11). GDD must specify: product id, type, price tier, payout (exact numbers), one-time vs repeat, shown-when rules for each offer (starter pack: after N minutes or first currency shortage; cooldown), restore behavior.

## 3. Daily login (V KT/ME 30-day, PB 7-day)

KT/ME (doc 05 sec 6): `Data_DailyLogin{StartUtcDay, claimed per day}`, 30 `Daily_Login_Asset` in `Configs/DailyLogin`, calendar-based (no streak reset), states Locked/Today/Missed/Claimed, missed day recoverable by rewarded ad (placement 1201). PB (V `DailyReward/DailyRewardConst.cs`, `DailyRewardDataBlock.cs`, `DailyRewardHelper.cs`): 7 days, `DayDuration = 23 h` (not 24: lets the player claim slightly earlier each day), `DailyRewardDataBlock{DateTime _time, int _index}`, `IsReadyToClaim = UtcNow - time >= 23h`, `NextDay()` debug shift, reward types `Currency / CurrencyPlus / CharacterSkin`, `DailyRewardNotification` (red dot).
Weakness (I): both trust the device clock (`UtcNow`), so a clock change claims all days. Local-only standard: store `lastClaimUtc` AND `lastSeenUtcMax`; if `UtcNow < lastSeenUtcMax - 5 min` treat as tampered (freeze claiming until clock catches up); never reward more than 1 claim per real 20 h of elapsed monotonic time (`Stopwatch`/`Time.realtimeSinceStartup` across the session). Streak variant for the clone: 7-day loop with day-7 big prize; 23 h unlock window; missed day = reset to day 1 or ad-recover once (design choice, GDD must state).
GDD must specify: cycle length, reset rule, unlock window (23 h vs calendar day), reward per day (type, amount, ad-double?), missed-day behavior, red-dot rule, first-day popup timing (not before FTUE end).

## 4. Spin wheel (GAP: only slot machine exists)

V reference: `Factory_Jackpot` + `Jackpot_Spin` (doc 05 sec 7): outcome rates No/Double/Triple 0.15/0.60/0.25, pity after 10 misses, level-gated tables, 1 free spin/day (+1 VIP), IAP spin SKUs 3.99/26.99/96.99. KT displayed-vs-real odds mismatch (Ascended 0.0001 vs 0.5) is a store-policy risk.
**Standard wheel (I):** `Wheel_Asset{ id, slots[{rewardType, amount, weight, color, displayChance}] }` (8 slots), `Data_Wheel{ lastFreeSpinUtcDay, freeSpinsBanked, adSpinsToday, pityCounter }`, `Factory_Wheel`. Flow: free spin daily (resets UTC day), extra spins via rewarded ad (max 3-5/day, placement `Wheel_ExtraSpin`), result chosen BEFORE animation (weighted + pity), animation lands deterministically (ease out over 3-4 s, 5-8 turns + target angle), reward granted on stop with currency spread. Rules: displayed chance == real weight; jackpot slot weight <= 2%; no unlimited paid spins without disclosed odds. Events `wheel_open`, `wheel_spin{source=free|ad|iap}`, `wheel_reward{slot,type,amount}`. UI: wheel, pointer, 8 slot labels, Spin button (free), "Watch ad" button (state: cooldown/limit), result popup, red dot when a free spin is available. GDD: slot table, weights, free/ad/iap spin counts, pity.

## 5. Quests, achievements, badges (GAP)

V: none. `Quest_Arrow/Focus_Msg/Focus_Pointer/Zoom` are tutorial guidance (ME `Logic/Quest`, KT `Logic/UI`), not a quest economy (doc 05 sec 9). RAP has a Ranking popup with an "Achievements" tab shell (V `PanelRanking.cs`: `btnAchievement`, `btnAchievements`) and Feel's `MMAchievementManager` plugin (V files exist, I: unused by game).
**Standard (I):** one stat-driven system.
- `Stat_Type` enum (`EggsHatched, PetsOwned, CoinsEarned, SessionsPlayed, Deaths, DistanceWalked...`) + `Data_Stats{ Dictionary<Stat_Type,double> }` incremented through ONE `Stats.Add(type, amount)` that also posts `Event_Stat_Changed(type, total)`.
- `Quest_Asset{ id, stat, target, reward, period(Daily|Weekly|OneTime), unlockLevel }`, `Achievement_Asset{ id, stat, tiers[{target,reward}], badgeSprite }`, `Factory_Quest` registry.
- `Data_Quest{ activeDaily[3], dailyResetUtcDay, progress, claimed, weeklyResetUtcWeek }`; reroll one daily quest via rewarded ad.
- Subscribe once to `Event_Stat_Changed`; no per-quest `Update`. Badges = cosmetic unlock when achievement tier done (title/icon shown on profile/leaderboard).
- UI: Quest popup (3 rows, progress bar, Claim, ad-reroll), Achievement list (tiers), red dot on HUD button, toast "Quest complete".
- Tuning: daily set = 1 easy (~2 min), 1 medium (~8 min), 1 long (~20 min); reward ~15-25% of a day's earnings; weekly chest on 5 of 7 completed.
GDD: stat list, quest pool with targets/rewards, reset time, achievement tiers, badge art list.

## 6. Codes / redeem (GAP; local-only constraint)

V: none in any project. Without a server, codes cannot be revoked or counted.
**Standard (I):** `Codes_Asset` list shipped in build: `{ codeHash (SHA-256 of upper-cased code + salt), reward, expiresUtc, maxUsesPerDevice=1 }`; the plain code is never in the build. `Data_Codes.redeemed: HashSet<string>` of hashes. UI: input field (uppercase, trim, 20 chars), Redeem, results `Success / AlreadyUsed / Invalid / Expired`. Code distribution is marketing (video descriptions); to rotate codes ship them via remote config JSON (`codesJson`) if the project has Firebase RC; otherwise per app update. Rate-limit: 5 wrong tries then 60 s lock. Events `code_redeem{result, code_id}` (log code_id not the code). GDD: code list, rewards, expiry, where the button lives (Settings or Shop), marketing plan.

## 7. Rating prompt (V)

KT/ME (V `Logic/Rating/RatingHelper.cs`, `Rating.cs`, `Data/Data_Rating.cs`): `Data_Rating{RatingDone (persisted), RatingInThisSession (reset each launch), RatingCount}`. `CanShow = !RatingDone && !RatingInThisSession && TutorialCompleted`. Triggers: tutorial completion (`SKB_Tutorial.CompleteTutorial`), after a revive was declined (`Result_Revive_Killed`), ME `GameManager` and `MonkeyEscape_Master` (win flow). Two-button popup (Good/Bad): Good -> `AppStore.Review()` (Android only; iOS branch empty) and `RatingDone=true`; Bad -> only the session flag (so it asks again next session, forever; weakness). Bounce SDK `PopupRating` (V): 1-5 stars, 5 stars opens the Play Store URL, `hasRated5Star` PlayerPref, 300 s min interval via `pref_rating_last_show`.
Standard (I): ask once after a "happy moment" (finishing a level/stage, claiming a big reward), never after a death/fail, never in the first session; cap at 3 asks total with >= 3 days between (`ratingCount`, `lastAskUtc`); Bad -> offer "send feedback" instead of store; use the native in-app review API (Google Play In-App Review / `SKStoreReviewController`) rather than opening the store URL. GDD: trigger events, session/day minimums, max asks.

## 8. Settings, pause, privacy

V: KT `Logic/Settings/Settings.cs` + `Settings_Toggle` (Music/Sound/Vibration; `DataSettings.MusicVolume`, `SoundVolume` floats 0/1, `Vibration` bool), `Settings_Language_Item`, popup board 800x650, `Btn_Home` hidden on Home scene (`GameConstants.SCENE_HOME`), popup 0.3/0.2 s (doc 07 sec 5 #1). TBE `Core/Game_Settings.cs` binds `DataSettings` volumes to `AudioManager` in `RuntimeInitializeOnLoadMethod` with static reset on SubsystemRegistration (V; good pattern). Haptics: KT `Logic/Vibration/Vibration.cs` (Impact/Selection/Notification enums, reflection into Taptic, Android `vibrator` fallback), TBE `Core/Game_Haptics.cs` (`MIN_INTERVAL 0.08 s` throttle, Taptic Light/Medium/Success). Bounce legacy: `SoundManager.onSound/onMusic` PlayerPrefs (`BtnOnOffSound`), not DataBlock.
Gaps (I): quality setting (V: no UI; tiering is runtime `DevicePolicy`, doc 02/08), privacy row (policy URL, "manage ad consent", "delete data"), restore purchases button in Settings, version label, credits, support mail, **pause**.
**Standard Settings screen:** toggles Music, Sound, Vibration (+ master haptics throttle 0.08 s), Language (opens list with native names), Quality (Low/Med/High maps to URP asset + target fps 30/60; default from `DevicePolicy`), Notifications on/off, Restore Purchases, Privacy Policy, Terms, Manage Consent (re-opens UMP/MAX flow), Rate us, Contact support, Reset progress? (NOT standard; destructive, hide unless required), version `x.y (code)`. Data: `Data_Settings` DataBlock (`MusicVolume`, `SoundVolume`, `Vibration`, `QualityLevel`, `NotificationsEnabled`, `LocaleCode` in `Data_Localize` V). One binder class applies settings at `BeforeSceneLoad` and on value change (TBE pattern).
**Pause (GAP):** `Pause_Popup` sets `Time.timeScale = 0`, pauses audio mixer SFX group (music keeps at -10 dB), buttons Resume / Settings / Home / (Restart). UI tweens use `ignoreTimeScale` (V KT popups: `ignoreTimeScale 0`: i.e. NOT ignoring; so pause popup must set it true). Also auto-pause on `OnApplicationPause(true)` during timed activities; on resume re-sync timers from UTC. Block pause while a rewarded ad is showing. GDD: which screens have pause, whether pause stops income timers.

## 9. Offline earnings (V SAE only)

V `PetIncomeManager.cs` (lines 18-22, 108-156): `_offlineEnabled=true`, `_offlineCapHours=6`, `_offlineMinSeconds=60`, `_offlineMultiplier=0.15`. On cold start, elapsed time since last online tick (cap 6 h) -> `offlineGain = TotalPerSecond * 60 * offlineMin * 0.15` -> `DataMoney.AddPendingOffline`; `OfflineEarningPopup` shows `+X`, buttons Claim (x1) and Claim x2 (rewarded `AdsPlacement.Popup_OfflineEarning`=204), close = claim x1. `DataMoney.PendingOffline` persisted so the popup survives a kill. In-session pauses (ads, home) add directly without popup. `DataCage.CatchUpOffline` also advances egg incubation by elapsed time (V comment line 195).
Standard (I): store `lastActiveUtc` on pause/quit and every 30 s; on launch `elapsed = clamp(UtcNow - lastActiveUtc, 0, cap)`; reject negative (clock rollback) and ignore < min; pending value persisted before popup; popup after FTUE only; rewarded x2 (or x3 for VIP); show cap hours in the popup ("Offline earnings are capped at 6h"). Number ladder: 15% rate, 6 h cap (V SAE); consider cap upgrade as IAP/VIP (+2 h). GDD: offline rate, cap, min seconds, x2 rule, which systems progress offline (income yes, timers yes, enemies no).

## 10. Local notifications (GAP in games; framework exists)

V: framework `Runtime/Notification/Notifications.cs` (CodeSketch `com.codesketch@0fe9d8bab8cb`; SketchEngine `com.sketchengine@522ef3079890` same folder): `NotificationData{Id, Title, Body, Subtitle, DelaySeconds}`, `Notifications : MonoSingleton`, `ScheduleNotification`, platform handlers `NotificationsAndroid`/`iOS`, compiled only under define `CODESKETCH_NOTIFICATIONS` (+ `com.unity.mobile.notifications`, not in the inspected manifests, grep returned nothing). `OnApplicationFocus(false)` branch is an empty comment (schedule nothing) and focus returns call `CancelAll`. No game script in KT/ME `_Game` calls `Notifications.` (grep: 0).
**Standard (I):** schedule on focus loss from a `Factory_Notification` table: (a) daily reward ready (23 h after last claim), (b) free spin ready, (c) offline cap full (cap hours after pause), (d) egg/crop/timer complete (exact timestamps), (e) comeback D2/D3/D7 inactive. Limits: max 2 per day, quiet hours 22:00-08:00 local, localized strings from the Localization table (not hard-coded EN), Android 13 `POST_NOTIFICATIONS` runtime permission asked after first positive moment (not at launch), channel `default` + `reminder`; iOS permission request the same way; settings toggle cancels all. Events `notif_permission{result}`, `notif_open{id}`. GDD: notification list with trigger, delay, copy per locale, permission timing.

## 11. Analytics event taxonomy (single source `docs/analytics-events.md` per game)

**V today.** Transport `BounceSdk.LogEvent(name, k, v...)` (-> `log_evt`), `LogAds(type,state,placement)` (-> `log_ads`, 0.3 s debounce), `LogAdsRevenue`, `LogIAPSuccess` (receipt split, device only); Editor logs to console (doc 08 sec 5.4). Firebase compiled out (`USE_FIREBASE` undefined, V). Naming mixed. SAE (V `Logic/Monez/Log/LogHelper.cs`): `start_level{level}`, `win_level`, `lose_level`, `tut_start{step}`, `tut_done{step}`, `user_click{button}`, `unlock_zone{zone}` (once, persisted in `DataAnalytics._unlockedZones`), `steal_start/success/fail{egg}`, `monster_caught`, `upgrade_treadmill/base{level}`, `speed_milestone{recommend}` (persisted milestone idx), `reset_day{reset}`, `user_drop{check}`, `iap_click/payment_done/payment_fail{product_id}`. KT/ME: `{minigame}_{world}_Checkpoint`, `payment_start/done/fail`, `trail_purchase`, `aura_purchase`.
**`user_drop` pattern (V SAE `UserDropTracker.cs`):** `Mark(check, hold)` writes the check to disk and clears after 10 s (or holds during an ad); `ReportPendingOnLaunch()` in `GameManager` logs `user_drop` when the app was killed while a check was active. Checks: `monster_attack`, `inter_show`, `reward_show`, `place_egg`. This is the only crash/ANR/rage-quit signal in the projects (see 19).

**Standard taxonomy (I; names lower snake_case, params snake_case, max 6 params, no PII):**

| Group | Event | Params | Fired where |
|---|---|---|---|
| Session | `session_start` | `session_n, days_since_install, locale, device_tier` | boot after init |
| FTUE | `ftue_step` | `step_id, step_n, seconds_since_start` | each tutorial phase begin/end (`Event_Tutorial`) |
| FTUE | `ftue_complete` | `seconds, deaths` | `CompleteTutorial` |
| Progress | `level_start/win/lose` | `level, mode, attempt` | level flow |
| Progress | `zone_unlock` | `zone` | once, persisted |
| Economy | `currency_earn` | `currency, source, amount` | Data layer grant (aggregate per 30 s, not per tick) |
| Economy | `currency_spend` | `currency, sink, amount, balance_after` | purchases |
| Economy | `upgrade` | `type, level, cost` | upgrade buy |
| Ads | `ad_offer` | `placement` | button shown |
| Ads | `ad_show` / `ad_complete` / `ad_fail` / `ad_close` | `format, placement, reason` | `AdsHelper` only |
| Ads | `ad_revenue` | `format, network, value_usd` | SDK paid event |
| IAP | `iap_view` -> `iap_click` -> `iap_success` / `iap_fail` / `iap_cancel` | `product_id, price_usd, source_screen` | `IAP_Purchase_Button` / receiver |
| Meta | `daily_claim`, `wheel_spin`, `quest_claim`, `code_redeem`, `offline_claim{multiplier}`, `rating_ask/rating_result`, `notif_permission` | see sections | meta systems |
| Settings | `setting_change` | `key, value` | settings |
| Health | `user_drop`, `save_recovered`, `save_reset`, `update_prompt` | `check` / `source` | boot + trackers |

Funnels to build in the dashboard: **FTUE** `ftue_step 1..N -> ftue_complete -> level_start(2) -> session_start(2)`; **Ads** `ad_offer -> ad_show -> ad_complete` per placement + revenue per DAU; **IAP** `iap_view -> iap_click -> iap_success`; **Economy** earn/spend balance by source, sink coverage; **Retention** D1/D3/D7 from `session_start`. Rules: payer flag from `Data_IAP.TotalPurchaseCount` (V) attached as user property; each persisted "once" milestone uses a persisted max (V pattern in ME checkpoints and SAE speed milestone); Editor logs only; add new events only by editing the taxonomy file first (`monetization-integration` already requires this, V skill text). GDD must list the events it needs per feature.

## 12. Remote config usage (V, with local-only caveat)

V: `RemoteConfig.CONFIG` priority Server -> Firebase -> local asset (`Resources/.../LocalRemoteConfig`) -> code defaults (doc 05 sec 1, `RemoteConfig.cs` `LOCAL_REMOTECONFIG` loaded in `Init`, `isFirebaseLoaded`, `eventLoadConfigComplete`). Keys actually used: ad timings, `listInterConfig[]`, `upAppVersion`, `logEnable`, `adsBreakEnable`, game-side `breakAdsInterval`, `isInternetRequiredEnabled`, `iapVariantConfigStr` (A/B price variants). Firebase is disabled in KT/ME, so shipped config = local asset + defaults (live values unverified).
Standard for local-only (I): Firebase Remote Config only (no custom server): fetch on boot with 12 h min interval, `FetchAndActivate` with 3 s timeout, last-good values cached by RC itself; every key has a code default (game works with RC unreachable); typed accessors in one `Config_Remote` static; keys: ad timings, placement enables, IAP variant map, reward amounts for ad rewards, `forceUpdateMinVersion`, `softUpdateVersion`, `maintenanceMessage`, `codesJson`, feature flags. Never gate FTUE on RC arrival. Version-gate risky experiments on `session_n`. GDD lists each tunable with default and allowed range.

## 13. Localization pipeline (V KT/ME)

V (doc 07 sec 2, doc 08 sec 8): Unity Localization 1.5.12; one table `LOCALIZE` + `LOCALIZE_<code>` per locale as Addressables groups (no remote content); 9 locales `en, vi-VN, ja-JP, ko-KR, ar-EG, ar-SA, es-MX, tr, uk-UA`; code `LocalizeKey` (const strings), `Factory_Localize` (Get, GetNativeName, `EnsureLocaleInitialized` detects `Application.systemLanguage` once and persists in `Data_Localize.LocaleCode`), `Factory_Localize_Font`, `Factory_Localize_Number`; components `Localize_TMP_Text`, `Localize_TMP_Text_Format` (`{0}` args), `Localize_TMP_Font`; RTL via RTLTMPro; settings language picker (`Settings_Language_Item`, `Setttings_Language`). Fonts per locale (V): Nunito-Bold (latin), Jua (ko), MPLUSRounded1c (ja), AligarhArabic (ar); base display fonts `UTM AvoBold SDF`, `ChangaOne SDF`. Glyph preload tool `Localize_GlyphPreloader` (Ctrl+U `Tools/Localize/Force Load All Glyphs Into Atlas`, `Export Required Characters Per Font`; V doc 08). Number format: `BigNumber.ToCompactString()` K/M/B and `Factory_Localize_Number` (locale-specific separators/suffix; behavior I). TBE/SAE/PB/RAP/TRW: no localization found (V grep), so those games ship English-only strings.
**Translation workflow (I, closes gap):** (1) strings authored only via `LocalizeKey` in code/prefab, never baked into prefabs; (2) Editor tool exports `LOCALIZE` to CSV (key, en, context, max_chars, screen); (3) translators/LLM fill locale columns with glossary (currency names, "Egg", brand terms untranslated), plural rules and `{0}` preserved; (4) import CSV back; (5) lint tool: missing keys per locale, `{n}` mismatch, length > max_chars * 1.4 (de/tr/vi expand), forbidden chars; (6) glyph preload per font run before build; (7) QA screenshot pass at longest locale and at ar RTL. Fallback chain: locale -> en. Arabic: RTLTMPro fixes shaping, mirror layout only where the design needs it (progress bars stay LTR, numbers stay LTR); font with Arabic glyphs must be a TMP fallback. Priority locales for a Roblox-clone audience (I): en, es, pt-BR, ru, id, tr, ar, vi, fr, de (ja/ko if the art suits). GDD must specify: locale list, string table owner, max lengths per UI slot, whether currency/number format is localized, store listing locales.

## 14. Tutorial / FTUE (V)

KT (V `SKB_Tutorial.cs`): phase int in `Data_SpeedKeyboard`, phases 1-4, `TUTORIAL_DONE_PHASE` completes + migrates old saves, level-gated phase 4 arrow (level >= 8), spotlight `Quest_Focus_Msg`/`Quest_Focus_Pointer` (doc 07 sec 1.3: 4 dim masks around a 325x125 hole, hole shrink `DOVirtual.Float(1,0)` OutSine, world-target follow in LateUpdate), `UINotificationText.Push(MsgTutorialComplete)`, completion enables `Data_Shop.EnsureBoostRestocked` and triggers `RatingHelper.Show`. ME (V `Data/Data_Tutorial.cs`): `{Phase=1, Completed, Phase1RewardGranted, TrailRewardGranted, AuraRewardGranted}` (each reward granted once, persisted). TBE (V `Data/Data_Tutorial.cs`, `Logic/Tutorial/*`): `Tutorial_MainPhase` enum BreakEgg=0, StealAnimal=1, PickUpPet=2, ReturnToCage=3 persisted int; sub-tutorials Trail/Treadmill/Cage as booleans, `PickupFocusShown`, `Tutorial_HudVisibility` (hides HUD parts until introduced), `Tutorial_Protection` (damage immunity), `Event_Tutorial`. SAE (V `DataTutorial`, `TutorialManager`): `Tut1Done/Tut2Done/TutEquipBestDone`, line renderer guidance (`TutorialLineRenderer(Anim)`), `TutorialBannerPopup`; **ads blocked until Tut1+Tut2 done** (V `AdsHelper`).
Standard FTUE flow (I): boot -> splash -> (privacy/consent) -> first scene directly in gameplay (no menu) -> action in < 10 s -> reward within 60 s -> introduce one system per phase, HUD hidden until introduced (V TBE) -> first purchase/upgrade -> first progression unlock -> end popup + rating AFTER (V KT) -> daily login popup only on session 2 (I). Data: phase int + per-reward flags; resume-safe (re-enter shows the current phase; V KT phase 4 re-point). Skip nothing the player can break: protect from damage (V TBE), lock currency sinks (I). GDD must specify: phase list with trigger/exit, what is hidden/locked per phase, reward per phase, copy keys, failure recovery (re-show arrow after 8 s idle, I), analytics step ids.

## 15. Loading / splash (V)

V: Bounce `Splash.unity` is build index 0: studio logo 2 s then loading bar 5 s (doc 08 sec 5.2), `PopupPrivacy.CheckNeedShow` on first launch (init only after accept), `BounceSdk.InitOnStartup` idempotent, next scene `LoadSceneAsync(1)`. In-game `LoadingScreen` (`Logic/Scene/LoadingScreen.cs`, doc 07 sec 1.3): fade 0.25 s, real progress to target then fake fill to 100% over `_finalizeDuration 1.5 s`, minimum hold, bar 834x83. TBE has `Logic/Loading`. Standard (I): total cold-start budget <= 4 s to interactive on low-end; logo <= 1.5 s; never block on SDK/ads init (init in background after first frame); show privacy/consent first on first launch only; preload critical Addressables + glyph atlases + pool warm behind this screen (doc 02 rule on one-time costs); tips text from Localization, rotating every 3 s. GDD: boot order, tips list, loading art.

## 16. Leaderboards with bots, friends/invite substitutes, share

V: no real leaderboard in KT/ME (only SDK message classes `CSLeaderBoard{leaderBoardId, from, to, properties}`, `SCLeaderBoard{userInfos[]}`, `SCUpdateRank`, `CSUpdateProperty` in `BounceSdk/`; UI absent, backend not verified). RAP/SAE (V `PanelRanking.cs`, `SlotUserRankInfor.cs`): fake leaderboard, 1000 unique names generated by shuffling a first-name pool (`FakeUserCount=1000`, `GetFakeUserNames()` cached), rows get rank = index+1 and top 3 shown on a podium; tabs "Play time / Richest / Achievements"; **scores are not real** (no player row, no values found; I).
**Standard local fake leaderboard (I):** `Leaderboard_Asset{ id, statSource, botCount=50, scoreCurve, refresh=daily }`; bots generated deterministically from `seed = dayIndex + boardId` (name pool x locale-aware pools, avatar from skin list, score = lognormal around the player's stage with a long tail), so the board is stable within a day and changes daily; player always inserted with the real stat, placed realistically (aim top 10-30% early to motivate, drift down as the player's stat plateaus); weekly reset with rewards (top 3/10/100 chest) paid from `Data_Leaderboard{ lastPaidWeek }`; bots tick up slowly in-session (random +0.5-2%/min) so the board feels live. Disclose nothing misleading in store text (policy: fake social proof can be flagged; keep it "Rankings" not "Global players", I). If a real board is ever wanted, platform services (Google Play Games / Game Center) are the no-server option.
**Friends/invite (I):** none; substitute with (a) "Share" native sheet with referral-less text + store link (`NativeShare`-style plugin or `Application.OpenURL` mailto/sms fallback), reward claimable once/day without verification, (b) bot "friends" list inside the leaderboard (names + gift button: claim a daily free gift from 3 bot friends, rewarded ad doubles it), (c) "Invite 3 friends" quest fulfilled by share-action count (honor system, small reward only). Never promise real multiplayer. Share (I): screenshot of result card (render a RenderTexture of the pet/egg/stat) + `Application.identifier` store URL; event `share{target}`.

## 17. App update / force update (partial)

V: only `RemoteConfig.upAppVersion` + `IsUpAppVersion()` (compares `AppUtils.GetAppVersion()` with a config int; used to disable ads for the version under store review, V lines 36-37, 191-195) and `GuiTextAppVersion` (PB version label, V). No force/soft update UI found.
**Standard (I):** RC keys `minSupportedVersionCode` (force), `latestVersionCode` (soft, once per 3 days). On boot compare with `Application.version` build code; force -> blocking popup "Update required" with Store button (`market://details?id=<package>` fallback https), no dismiss; soft -> dismissible popup with the update reward optional. Prefer the Google Play In-App Updates API for Android if the plugin is already present (I; optional). Always allow the game to start if RC unreachable. Event `update_prompt{kind, shown_version}`. GDD: min version policy, who owns the store URL.

## 18. Save corruption recovery (GAP; framework facts V)

V framework `DataFileHandler.cs` (CodeSketch `Runtime/Data`): `Save` serializes, skips the write when the FNV-1a 64-bit hash equals the last write, then `WriteAtomic`: write `<file>.tmp` then `File.Replace(tmp, file, null)` (fallback `Delete` + `Move` if Replace fails on Android filesystems). `Load` returns **null on any exception or missing file**, and callers create a fresh block, so a corrupt file silently becomes a brand-new save; `File.Replace(..., null)` passes no backup name so there is no `.bak`. SketchEngine v2 adds autosave 2 s debounce + background thread (doc 01 sec on versions). SAE uses MemoryPack-serialized `DataBlock`s (V `[MemoryPackable]`), binary and schema-fragile.
**Standard (I):** (1) keep the last good file as `<file>.bak` (pass a backup name to `File.Replace`, or copy before replace) and rotate a daily `.bak1`; (2) add `[magic][version][length][crc32]` header around the payload; (3) on `Load` failure or CRC mismatch: try `.bak`, then `.bak1`, then new save, logging `save_recovered{source}` / `save_reset`; (4) show one non-blocking toast "Progress restored from backup" and never silently wipe; (5) schema migrations by `version` int with a migration chain (not `InitializeOnLoadMethod`, doc 08 anti-pattern `Add_VIP_Jackpot_Benefit`); (6) never rely on PlayerPrefs for important state (Bounce `SoundManager` uses it only for toggles, V); (7) Editor menu "Tools/Game/Save/Open folder, corrupt current save, restore backup" for QA. Local-only means no cloud backup: optionally Google Play Games Saved Games or Auto Backup (`android:allowBackup=true` with a backup-rules XML that includes the data folder; I). Test cases for `playmode-script-testing`: kill during write, truncated file, zero-byte file, wrong version.

## 19. Crash / ANR handling basics (GAP)

V: none beyond SAE `user_drop` (rage-quit/kill proxy) and SDK debug log. Firebase Crashlytics not active (Firebase compiled out).
**Standard (I):** (a) Firebase Crashlytics (free) in every release build OR Unity Cloud Diagnostics; custom keys `session_n, level, locale, device_tier`; log breadcrumbs from `Event_*` posts at low volume; (b) `Application.logMessageReceived` -> count exceptions per session, rate-limit duplicates (max 3 per message), show nothing to the player; (c) ANR avoidance rules already in the performance docs: no sync load > 100 ms on main thread, no blocking save on pause (SketchEngine autosave thread V), ads init off the first frame; (d) `OnApplicationPause(true)` saves + stores `lastActiveUtc`; (e) a "safe boot" flag: write `bootInProgress=true` before init and clear after first frame; if the next launch finds it set 2x in a row, skip optional systems (ads preload, notifications) and log `safe_boot` (I); (f) Android vitals watch: ANR rate < 0.47%, crash < 1.09% (Play thresholds, I); (g) `user_drop` pattern from SAE for forced kills during ads/popups. GDD: crash tool choice and release gate (no release if crash-free sessions < 99%).

## 20. Gaps no project covers + standard solution (summary)

| Gap | Standard solution | Section |
|---|---|---|
| Provider-agnostic ads with fake Editor ads and consent state | 3 layers: provider adapters / `AdsPolicy` / `AdsHelper` facade; `AdsProvider_Fake` overlay; `IConsentService` | 1 |
| Spin wheel | `Wheel_Asset`, free daily + ad spins, result before animation, pity, honest odds | 4 |
| Quests / achievements / badges | One stat bus + `Quest_Asset`/`Achievement_Asset`, daily/weekly resets, red dots | 5 |
| Codes / redeem | Hashed shipped codes + `Data_Codes`, rate limit, RC list | 6 |
| Pause menu | `Pause_Popup` with timeScale 0 + audio group + ignoreTimeScale tweens | 8 |
| Quality / privacy / restore rows in Settings | One settings screen standard | 8 |
| Local notifications in games | `Factory_Notification` + permission after first positive moment + quiet hours | 10 |
| Central analytics taxonomy and funnels | `docs/analytics-events.md` + table in 11 | 11 |
| Fake leaderboard with real player row | Seeded daily bots, weekly rewards | 16 |
| Friends/invite/share | Share sheet + bot friends gifts + honor-system quest | 16 |
| Force / soft update | RC min/latest version + store popup | 17 |
| Save corruption recovery | CRC header + `.bak` rotation + migration chain | 18 |
| Crash / ANR basics | Crashlytics + breadcrumbs + safe boot + `user_drop` | 19 |
| Clock tampering for daily/offline | `lastSeenUtcMax` + monotonic elapsed cross-check | 3, 9 |
| Localization for non-KT/ME games (TBE, SAE, PB, RAP, TRW) | Reuse KT `LocalizeKey`/`Factory_Localize` stack from the start | 13 |

## 21. What a GDD must specify (checklist per system)

Ads: placements table, gates, remove-ads scope. IAP: product table and shown-when rules. Daily login: cycle, reset, rewards. Wheel: slots, weights, spin sources. Quests/achievements: stats, pool, targets, rewards, reset. Codes: list + rewards + expiry. Rating: trigger events and caps. Settings: rows, defaults, quality mapping. Pause: screens and timer behavior. Offline: rate, cap, x2 rule. Notifications: list, copy, timing, permission moment. Analytics: events per feature and funnels. Remote config: tunables with defaults. Localization: locales, length limits, fonts, owner. FTUE: phases, locks, rewards. Splash/loading: boot order, budgets. Leaderboard: stats, bot count/curve, weekly rewards. Share/invite: what is shared, reward. Update: min version policy. Save/crash: backup policy, crash tool, release gate.

## Proposed classification

| Candidate | Class | Proposed name | Must contain |
|---|---|---|---|
| Ads layering and facade contract | RULE | `ads-layer-contract` | provider/policy/facade split; only `AdsHelper` callable from gameplay; keys in ignored asset; rewarded callback exactly once; VIP keeps rewarded; FTUE ad-free; placement int enum logged by name |
| Fake Editor ads + consent service | RECIPE | `recipe-ads-fake-provider` | overlay with reward/close/no-fill/fail switches; `IConsentService` states; debug menu rows |
| Meta systems complete-game checklist | SKILL | `meta-systems-checklist` | the section 0 matrix as a go/no-go list per game; which systems are mandatory/optional by genre; links to recipes below |
| Stat-driven quests + achievements | RECIPE | `recipe-quests-achievements` | `Stats.Add` bus, assets, Data, resets, UI, red dot, tuning ratios |
| Spin wheel | RECIPE | `recipe-spin-wheel` | slot asset, free+ad spins, pre-chosen result, pity, odds disclosure |
| Codes, offline earnings, notifications, daily login clock guard | RECIPE | `recipe-retention-timers` | `lastSeenUtcMax` guard, 23 h unlock window, offline formula with cap, notification table, codes hashing |
| Analytics taxonomy | RULE + DATA | `analytics-events-taxonomy` | table in section 11; naming rules; funnels; `user_drop` pattern; `docs/analytics-events.md` template |
| Localization pipeline | SKILL | `ui-localization` (EXTEND per docs 07/08) | `LocalizeKey` const, table export/import CSV, lint, font per locale, RTL, glyph preload, fallback chain, locale priority list |
| Save safety + crash basics | RULE | `save-and-crash-safety` | CRC header, `.bak` rotation, migration chain, recovery events, Crashlytics, safe boot, tests |
| Settings, pause, update, privacy screens | RECIPE | `recipe-settings-pause-update` | settings rows, pause behavior, force/soft update flow, privacy/consent re-open |
| Fake leaderboard and share | RECIPE | `recipe-fake-leaderboard` | seeded bots, player row placement, weekly rewards, share card |
| Tool: meta wiring audit | TOOL | `meta-wiring-audit` | scans for placements without call sites, analytics events not in taxonomy, LocalizeKey missing per locale, notification keys, Data blocks without Init `??=` |

**3-6 must-haves (priority order):** (1) `ads-layer-contract` + `recipe-ads-fake-provider` (every app, highest revenue risk); (2) `analytics-events-taxonomy` (cannot tune anything without it); (3) `save-and-crash-safety` (silent progress wipe is the worst player-facing failure; V framework returns null on corrupt load); (4) `recipe-retention-timers` (daily login, offline, notifications, clock guard, codes); (5) `meta-systems-checklist` (guarantees "complete games"); (6) `ui-localization` extension (only KT/ME localize; other 5 projects ship English-only).

Open items not traced (I): live remote config values, rating trigger in ME beyond the two call sites, PB/RAP/TRW ad and IAP wiring (Bounce files present, not read), whether RAP `PanelRanking` values are fake, real contents of `Factory_Localize_Number`, and `com.unity.mobile.notifications` presence per project (not in grep of manifests).
