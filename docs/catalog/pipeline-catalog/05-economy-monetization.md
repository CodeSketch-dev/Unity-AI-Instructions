# 05 - Economy, Progression and Monetization (reverse-engineered)

Sources: KT = `C:\Unity\GitProject\knife-tower\knife-tower-troll-unity`, ME = `C:\Unity\GitProject\monkey-escape\monkey-escape-unity`.
Paths are relative to `Assets/_Game/` unless stated. Tags: **V** = VERIFIED in cited file, **I** = INFERRED.

Framework note: CodeSketch and SketchEngine are the same framework (SketchEngine = renamed/optimized successor). Both projects here use the older `CodeSketch.*` namespaces (V: `using CodeSketch.Data;` in `Scripts/Data/Data_Currency.cs`) and singleton assets at `Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_*.asset` (V, both projects). In a SketchEngine project the concepts are identical but namespaces and the singleton loader path must be read from the installed package (I) - never hardcoded.

Important: the KT repo is really a **Speed Keyboard / treadmill** game (IAP ids `com.speed.keyboard.*`, `Data_SpeedKeyboard`, `SKB_*`), not a knife game (V: `Assets/Resources/IAPProductCatalog.json`). ME = Monkey Escape, same skeleton, world-based.

## 1. Architecture map (shared skeleton)

| Layer | Pattern | Evidence |
|---|---|---|
| Persistence | `Data_X : DataBlock<Data_X>`, `DataValue<T>` fields, static `Instance` proxy, `Init()` with `??=` | `Scripts/Data/Data_Currency.cs`, `Data_Shop.cs`, `Data_IAP.cs` (V) |
| Config | per-entry ScriptableObjects in `Configs/<Feature>/`, registered in `Factory_X : ScriptableObjectSingleton<>` | `Factory_DailyLogin.cs`, `Factory_Shop.cs` (V) |
| Events | `StaticBus<Event_X>.Post(new Event_X(..))` | `Event/Currency/Event_Currency_Spread_Start.cs` (V) |
| Popups | `PopupManager.Create(prefab)` from `Factory_*.ShowX()`; `HasInstance` guard prevents doubles | `Factory_IAP.cs`, `Factory_Gacha.cs` (V) |
| Ads | game wrapper `AdsHelper` -> `BounceAdsSdk` (Assets/BounceSdk) -> `AdsMAX`/`AdsAdmob`/`AdsIronSource` | `Logic/Ads/AdsHelper.cs`, `Assets/BounceSdk/BounceSdk/Ads/*` (V) |
| IAP | Unity IAP 5.4.1 (`StoreController`, `ConfirmedOrder`) + JSON ProductCatalog + `IAP_Product_Receiver` payout switch | `Packages/manifest.json`, `Logic/IAP/*` (V) |
| Remote tuning | `RemoteConfig.CONFIG` priority: Server -> Firebase -> local asset -> code defaults | `Assets/BounceSdk/BounceSdk/RemoteConfig.cs` (V) |
| Analytics | `BounceSdk.LogEvent/LogAds/LogIAPSuccess`, Firebase Analytics, static `LogHelper` wrappers | `Logic/Ads/LogHelper.cs`, `IAPManager.cs` (V) |

## 2. Currency

`Currency_Type` (V `Logic/Currency/Currency_Type.cs`): `Money=0, Gem=10, Cup=20, Ads=999, Free=8888, IAP_NoneConsumable=9001, IAP_Subscription=9002, IAP_Consumable=9003`. The last three plus Ads/Free are really "unlock/price kinds" reused by every shop item, not wallets.

| Wallet | Storage (KT `Data_Currency`) | Notes |
|---|---|---|
| Money | `Dictionary<Minigame_Type, DataValue<double>> _money` | per-minigame soft currency; `Get(Money)` keys on `Minigame_Static.Type` (V) |
| Cup ("entrophy"/trophy) | `Dictionary<Minigame_Type, DataValue<double>> _entrophy`; `Get(Cup)` hardwired to the SpeedKeyboard bucket | main premium-ish soft currency; IAP cup packs, jackpot trophies (V) |
| Gem | single `DataValue<double> _gem` | gacha price, "More Cup" rewarded popup reward (V) |
| Default grants | `_moneyDefaultGranted`, `_entrophyDefaultGranted`; `TryGrantDefaultEntrophy` | one-time starter grant per minigame (V) |
| World pickups | `_gemWorldCollectedFirstTime: Dictionary<string guid,bool>` | first-time-only gem pickups per world object (V) |

Amounts are `double`, displayed/authored as compact strings (`250K, 1.5M, 35T`) parsed by `UtilsNumber.ParseCompactNumber` (V `IAP_Payout_Parser.cs`) - incremental-game scale. ME `Data_Currency` has the same fields (V).
**Naming trap**: `Currency_MoreCup` popup says "cup" but grants **Gem** (V `Currency_MoreCup.cs`). Amounts `Factory_Currency._receiveMoreCupAmount=100`, `_receiveMoreCupBreakAds=100` (V `Game.Factory_Currency.asset`, both projects).

**Currency spread FX (V)**: bar `Currency_Bar`, `Currency_Bar_Spread`; event `Event_Currency_Spread_Start(type, amount, startPos, useBackground=false, renderCount=-1, mode=Preset, startIsWorldPos=false, itemScale=1)` + `Event_Currency_Spread_End`. Per-currency assets `Configs/Currency_Spread_{Cup,Gem,Money}.asset`: prefab, vfxEnd, sfxEnd, bezier controlStart (0,8) / controlEnd (6,-6), fadeIn 0.3 / fadeOut 0.2, sequenceDuration 0.5, backDuration 0.09, flyDuration 0.3, flyDelay 0.5, flyCurve, scaleDuration 0.5. Rule: **grant value to Data first, then post the spread event** (V `Shop_Cup_Reward_Item.cs`, `IAP_Product_Receiver.cs`).

## 3. Shop

`Shop_All_Type` (V): KT `Cup0, Trail10, Sound20, Skin30, Speed40, Offers60, Jackpot70, Aura80`; ME inserts `Aura=15`. `Factory_Shop.Show(Shop_All_Type)` opens `_shopAllPopup` on a tab (V `Shop_Stand_UI.cs`). Sold-out sorters `Shop_Offers_SoldOutSorter`, `IAP_Pack_Full_SoldOutSorter` (V names; behaviour I).

Item unlock/price kinds are `Currency_Type` on assets (`Shop_Boost_Asset._unlockType`, `Character_Skin_Asset.UnlockType`): Money/Cup/Gem spend a wallet (`Data_Currency.Get(type).Value < Price` -> toast `MsgNotEnoughGem` -> redirect `Factory_Shop.Show(Cup)`, V `Shop_Stand_UI.cs`); `Ads` (rewarded, `Shop_Skin_Item_Unlock`); `IAP_NoneConsumable`; `IAP_Subscription`; `IAP_Consumable` (V `Shop_Skin.cs`).

### 3.1 Rotating boost shop (core retention economy; V `Data/Data_Shop.cs`)
- Persisted: `_purchasedBoosts: List<{UUID,BoostID}>`, `_equippedBoosts`, `_boostCapacityLevel`, `_boostSlots`, `_boostNextRestockUtc` (ISO string), `_boostRestockCount`, `_boostItemNewNotification`, `_freeCupTodayLeft`, `_freeCupLastResetDate`. ME adds `_equippedBoostsByWorld`, `_boostSlotsWorldID`.
- Equip capacity = `BoostItemCapacity (5) + BoostCapacityLevel * BoostSlotPerPurchase (3)`.
- Purchase never auto-equips. `EquipBoost` fills an empty slot, else replaces the weakest (prefers a different BoostID); `EquipBestBoost` only on button press.
- Multiplier: `EquippedBoostMultiplier = sum(BoostValue)/100`; speed = `X * (1 + mult)`.
- Restock: 4 display slots, every 200 s; each slot rolls a Ranking independently from the weight table of the highest unlocked world; every 4th restock (`_boostVipWeightEvery`) uses the VIP table; very first restock is all Common and grants slot-0 item free. Stock per slot is random in `Factory_Shop.GetBoostStockRange(rank)`. Rewarded ad on sold-out forces restock (`Shop_Boost_Restock_Rewarded=303`, `ForceRestockNow`).
- Purchase validates slot stock AND lifetime `MaxStock`. IAP path decrements stock only if available and never blocks a paid transaction (V comments in `ConsumeBoostSlotStock`).

Restock weights, World 1 (V `Game.Factory_Shop.asset`; ME asset has 8 `_worldID` entries, same W1 values):

| Rank (enum value) | Common 0 | Uncommon 10 | Rare 20 | Epic 30 | Legendary 40 | Mythical 50 | Unique 60 | Ascended 70 |
|---|---|---|---|---|---|---|---|---|
| Base table | 49 | 40 | 5 | 3 | 2 | 1 | 0 | 0 |
| VIP table | 5 | 5 | 5 | 10 | 10 | 35 | 15 | 15 |

World 2 base: 10/30/22/20/7/6/4/1 (V). Weights need not sum to 100 (normalized in `RollRanking`).

KT boost assets (V `Configs/Shop/*.asset`): `boost.cart` rank30 +50 price 250M MaxStock 10 (Cup); `boost.crown` rank40 +100 5B max10 (Cup); `boost.cracky.sword` rank50 +39999 IAP consumable `mythical.item` max30; `boost.airplane` rank60 +69999 IAP max30; `boost.rocket` rank70 +99999 IAP max30. Items 1-3 (Cowboy Hat, Candy Armor, Cookie Backpack) not read (I: Common-Rare cup-priced). ME boosts are leaf/carrot/banana items in `Configs/Shop/Item_World_1..4` (V listing).

### 3.2 Free cup (rewarded)
`Shop_Cup_Reward_Item`: `FreeCupPerDay=5`, `FreeCupPerReward=100`; UTC key `yyyyMMdd` reset in `Data_Shop.EnsureDailyFreeGemReset`; button greyed via `Factory_Config.MaterialGrayScale`; placement `Shop_All_Cups_FreeCupToday_Reward=501` (V).

### 3.3 Other shop kinds (files V, behaviour I)
`Shop_Skin`, `Shop_Trail_*`, `Shop_Aura_*` (ME), `Shop_Sound_*` (sound pack IAP), `Shop_Speed_IAP_Item`, `Shop_Cup_IAP_Item`, `Shop_Jackpot_IAP_Item`, `Shop_Stand*` (in-world purchase stands with `Event_Shop_Stand_Timeup`, KT), `Boost_Fuse*` (ME), `Shop_Updater`.

## 4. IAP

**Stack (V)**: `com.unity.purchasing 5.4.1`. `IAPManager : MonoSingleton` (persists across scenes) wraps `IAPListener` (`onProductsFetched / onOrderConfirmed / onPurchaseFailed`). `IAPCatalog` loads `Resources/IAPProductCatalog.json` with `ProductCatalog.LoadDefaultCatalog()` at `BeforeSplashScreen`. `IAPConstants` holds payout subtype strings and fixed ids.

**Purchase flow (V `IAPManager.cs`, `IAP_Purchase_Button.cs`)**
1. UI `IAP_Purchase_Button` or `IAPManager.Purchase(productId, Action<bool>)`; id passed is the BASE id, resolved to the variant id by `IAPCatalog.ResolveProductId`; pending-dedup keyed on base id.
2. `ConfirmedOrder` -> `TryMarkTransactionProcessed(transactionId)` (dedupes several buttons bound to one product) -> `IAP_Product_Receiver.Receive(product, rectMoney)` switch on `payout.subtype`.
3. Non-consumables mark `Data_IAP.Purchase(baseId).Value = 1`; `Data_IAP.TotalPurchaseCount` flags payers for analytics.
4. Analytics: `BounceSdk.LogIAPSuccess(price, iso, productId, txId, receiptData, sign, params)` with Google receipt JSON/signature split by `ParseReceipt`, only `#if !UNITY_EDITOR`; per-button `LogHelper.IAPPurchaseClick/Success/Failed`.
5. **Restore** is entitlement based: on fetch every NonConsumable calls `StoreController.CheckEntitlement`; if `FullyEntitled` and `Data_IAP.Purchase(base)==0` -> `Receive`. `IAP_Button_RestorePurchased` is a cosmetic 3 s spinner (V) - an Apple-compliance placeholder (I).
6. Price text: `IAPManager.GetPriceText` -> `GameUtils.FormatPriceTrailingSymbol(product)`; "N/A" fallback; static event `OnProductsFetched` lets UI refresh from fallback to store price (V).
7. **Variant A/B pricing (V `RemoteConfig.Dev.cs`, `IAPVariantConfig`)**: remote JSON `iapVariantConfigStr` like `{ "carpet":"update", "skin.pack":"sale" }`; variant id = base + "." + variant; `IAPCatalog.FetchConfiguredVariants` dynamically fetches variant ids missing from the local catalog; ownership and data always keyed by BASE id.
8. Subscription: `IAP_Subscription` (+AutoRefresh, `Subscription_Countdown`) -> static facade `Subscription_VIP` (`IsActive`, multipliers read from catalog payout quantities with fallback 2/2, `RemoveAds`, `FreeRevive` max 5/day via `Data_SpeedKeyboard.VipFreeReviveUsed`, `OnChanged` event, `Refresh()` on resume). Perks follow subscription state, not one-time grants (V).

**Payout subtypes** (V `IAPConstants.cs`): `remove_ads` (sets `DataMaster.AdsBannerSkip` + `AdsInterSkip`, `BounceAdsSdk.SetRemoveAds(true)`), `carpet`, `weapon_deadlysword`, `infinity_hit`, `item_unlock_all`, `skin_unlock_all`, `skin_unlock` (matches `Character_Skin_Asset.IAPProductId`), `cup`, `speed`, `treadmill_x10/x200/x20K/ADMIN/GOD/INFINITY`, `keyboard_full_key`, `trail_infinity/star`, `aura_*`, `boost_item_unlock`, `boost_item_pack`, `boost_slot`, `jackpot_spin`; VIP: `cup_multiplier, exp_multiplier, skin_hospital, treadmill_special, remove_ads, free_revive`. Data field syntax `"<Total>, Bonus +<Bonus>"` compact (`IAP_Payout_Parser`). Fixed ids: `com.speed.keyboard.slot.item1`, `.vip.pass`, `.rebirth1`.

### 4.1 Real price table (V `Assets/Resources/IAPProductCatalog.json`, both projects; USD `googlePrice.num`; store tiers apply on device)
Product-id prefix `com.speed.keyboard.` in both projects (V). Types: t0 consumable, t1 non-consumable, t2 subscription.

| Group | Products -> USD (payout) |
|---|---|
| Remove ads | `remove.ads` 2.99; `.update` 4.99 |
| Carpet bundle (+remove_ads) | `flying.carpet` 4.99; `.update` 7.99; `.stand` 4.99; `.stand.update` 7.99 |
| Skin pack (+remove_ads) | KT `skin.pack` 5.99 / `.update` 8.99; ME `skin.pack` **16.99** / `.update` 8.99 / `.stand` 5.99 |
| VIP weekly sub (t2) | `vip.pass` 8.99; KT cup x2 exp x2; **ME cup x2 exp x5** |
| Cup packs (t0) | cup1 0.99=1,000; cup2 3.99=5,000; cup3 9.99=38,000 (ME 40,000); cup4 19.99=100,000; cup5 49.99=400,000 (ME 300,000); cup6 69.99=40M+20M; cup7 99.99=10B+5B; cup8 169.99=2T+1T; `.stand` offers cup2/5/7 |
| Speed packs (t0) | sp1 0.99=250K; sp2 3.99=1.5M; sp3 9.99=9M; sp4 29.99=30M; sp5 49.99=500M; sp6 69.99=35B+15B; sp7 99.99=35T+15T |
| Treadmill unlocks (t1) | x10 2.99 (ME 8.99; `.update` 8.99); x200 34.99; x20K 44.99; ADMIN 16.99 (`.update` 24.99); GOD 39.99; INFINITY 99.99 |
| Cosmetics (t1) | skins: jett 2.99, demonhunter 3.99, alice/yuki 4.99, ruby 4.99 (t0), kurama 5.99, ghost/punchman 6.99, bella/lilith 7.99, hades/spider 9.99, nightwing 12.99; aura infinity 49.99, goku 89.99 (KT) / 69.99 (ME); trail infinity 89.99; trail star 99.99; sound pack 19.99 (KT) / 59.99 (ME) |
| Boost items (t0) | mythical 39.99; unique 69.99; ascended 99.99; `item.pack` 99.99 (t1, 2 named boosts); ME adds world-4 variants 69.99/89.99/99.99 and singles 9.99-39.99 |
| Boost slots (t1) | KT `slot.item1` 0.99 flat (+3 slots per purchase, unlimited); **ME ladder item1..9 = 0.99, 1.99, 2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99** |
| Jackpot spins (t0) | `slot.machine` 3.99 (1); `slot.machine9` 26.99 (9); `slot.machine49` 96.99 (49) |
| Rebirth skip (t0) | `rebirth1` 0.99 (ME also `rebirth2` 1.99) |
| ME world unlock (t1) | `map.2/3/4` 9.99 each (`world_unlock`) |

Skeleton: price ladder 0.99/2.99/3.99/4.99/9.99/19.99/49.99/69.99/99.99(/169.99); top tiers add a ~50% "Bonus" on top; whale anchor 99.99; `.stand` and `.update` suffixes = same payout, different placement or price test (V names; I intent).

## 5. Ads

### 5.1 Integration points (V)
- `AdsHelper` (KT `Logic/Ads/AdsHelper.cs`; ME `Logic/Monitize/AdsHelper.cs`): `ShowBanner/HideBanner`, `ShowInterstitial(AdsPlacement|string)`, `ShowInterstitial(onClosed, placement)`, `ShowRewarded(Action<bool>, AdsPlacement)`, `IsInterstitialOKToShow`, `IsRewardReadyToShow`, `IsAdsRemoved`.
- Skip rules: `BannerSkipped = DataMaster.AdsBannerSkip || Subscription_VIP.RemoveAds`; `InterSkipped` likewise; **rewarded is skipped only by `DataMaster.AdsRewardSkip`** (callback gets true) - VIP does NOT remove rewarded ads.
- Rewarded contract: `UI_Internet_Manager.RequestCheck()`; not ready -> toast "No ads available at the moment" + `callback(false)`; **Editor always returns true**.
- Compile defines `USE_BOUNCE_SDK`, `USE_FIREBASE`, `MAX` (AppLovin MAX; `ADMOB` alt branch). SDK in `Assets/BounceSdk/BounceSdk/Ads/` (AdsMAX, AdsAdmob, AdsIronSource, BounceAppOpenManager, MaxNativeAds).
- Banner shown on gameplay entry: `GameManager` (5 sites), `Character_Checkpoint`, `Tower_Master`; hidden when VIP flips on (`Subscription_VIP.OnChanged`).

### 5.2 Interstitial gating (V `BounceAdsSdk.IsInterstitialOKToShow`, `RemoteConfig.cs`)
Order: not removed -> placement not blocked (`listInterConfig[placement].enable`) -> not "up app version" -> `sessionToShow <= session` -> seconds since first open >= `timeStartToShowInter` (**code default 60**) -> seconds since last inter >= `timeBetweenShowInter` (**default 40**) -> ad ready. Per-placement override `InterstitialConfig{placement, timeStartShow=60, timeBetween=30, sessionToShow=1, enable=true, adsBreakEnable=true}`. Other defaults: banner start 60 s, app-open start 60 s, native start 60 s, collapsible banner gap 30 s, `adsBreakEnable=true` shows the `AdsLoading` screen before an inter. Live values come from Server/Firebase (I: no local remote-config asset found in either project, so code defaults are the verified floor).
- Game-side extras (V `RemoteConfig.Dev.cs`): `breakAdsInterval=60`, `speedKeyboardBreakAdsInterval=60`, `paintKeyboardBreakAdsInterval=60`, `isInternetRequiredEnabled=true`.
- ME adds `MinimumInterstitialLevel=10`: `ShowInterstitialWithNative` only fires when `Data_MonkeyEscape.Level >= 10`, then chains a native fullscreen ad (`Monetize_AdsNativeManager.RequestAfterNextInterstitial`); `IsNativeAdsEnabled = remote flag && !IsAdsRemoved` (V).

### 5.3 "Break ads" flow (V `Ads_InterstitialAdsBreak.cs`, `Currency_MoreCup.cs`, `AdsBreak_Static.cs`)
`Update` accumulates time; at `breakAdsInterval` (60 s), if `IsInterstitialOKToShow` -> `AdsBreak_Static.ShowCurrencyBreakAds()` opens a "+100 gems, watch ad" popup (`_isBreakAds=true`). Watch = rewarded (`Shop_Currency_MoreCup_BreakAds=602`); Close = popup closes, then an **interstitial** plays. If no inter ready, polls every 1 s. Mutual-exclusion statics `SPEED_POPUP_RESERVED_OR_OPEN`, `NO_ADS_POPUP_RESERVED_OR_OPEN`, reset in `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]`. After **3 completed interstitials** per session (`NO_ADS_POPUP_INTERSTITIAL_COUNT=3`) the NoAds IAP popup shows once per session; Speed-pack popup at most once per session.

### 5.4 Placement catalog (V `AdsPlacement.cs`; KT ~38 values, ME 51 lines)
Result/revive 101-103; shop stand 301-303 (303 = boost restock rewarded); skin unlock 401; free cup 501; MoreCup 601/602; LuckyBox skip cooldown 801; StealAPet 901-907 (legacy); SpeedKeyboard 1001-1008 (treadmill VIP, entropy x2, speed multiplier, rebirth skip, teleport, speed-pack close, return stage); PaintKeyboard 1101-1105; DailyLogin missed day 1201. The enum NAME string is what is logged and configured remotely. Death / revive-cancel / checkpoint interstitials use `Minigame_Type` extension strings (`ToDeath()`, `ToCheckpoint()`, `ToReviveCancel()`) (V `Player.cs`, `Result_Revive_*`, `EasyObby_Player.cs`).

Rewarded call sites (V grep): MoreCup, Daily missed day, free cup, boost restock, stand item/skin, skin unlock, revive (`Result_Revive_Stage/Checkpoint/SkipCheckpoint`), rebirth skip, teleport, treadmill, entropy/money x2, upgrade/worker buy, `BoosterButton`, `EasyObby_GUI`. Interstitial sites: death, revive cancel, checkpoint, return stage, treadmill speed-pack close, MoreCup close.

### 5.5 Revive (V `Subscription_VIP.Revive`, `Result_Revive_*`)
Timed popup (`_sequence` paused while the ad plays); button -> `AdsHelper.ShowRewarded` (VIP free revive up to 5/day skips the ad) -> success: on `Popup.OnCloseEnd` post `Event_Character_Revive_Checkpoint`; fail: resume sequence + `MsgWatchAdsFail`; Give up/close -> interstitial `ToReviveCancel`. `Factory_Result.ShowReviveCheckpoint` routes SpeedKeyboard -> stage revive, others -> checkpoint revive; `SetFreeRevive(VIP)` swaps the ad icon.

## 6. Daily login (V)
`Data_DailyLogin` (`StartUtcDay` + claimed flag per day via `Get(day)`); `Factory_DailyLogin`: `_configs: Daily_Login_Asset[]` (30 assets `Configs/DailyLogin/Daily_1..30`), frames per day type, popup prefab. Day index = `min(UTCday - StartUtcDay, count-1)` - calendar-based, no streak reset. States `Locked/Today/Missed/Claimed`. Today = free claim; **Missed = rewarded ad to recover** (`DailyLogin_MissedDay_Rewarded=1201`). Flow `Daily_Login.TryClaim -> CompleteClaim -> Daily_Login_Reward_Receiver.TryReceive`. Reward enum `Trophy0, Speed10, Trail20, Skin30, Keycap40, JackpotSpin50, BoostItem60`; day type Normal/Premium/Special picks the frame. Editor-only `AdvanceDebugDays`. `_rewardValue` is a compact string only for Trophy/Speed.

KT table (type letter T=Trophy S=Speed R=Trail K=Skin C=Keycap J=JackpotSpin B=BoostItem; frame N/P/Special*):
d1 T10 | d2 S25K | d3 R P | d4 T200 | d5 B | d6 S100K | d7 C* | d8 T3000 | d9 B | d10 S3M P | d11 S500K | d12 T7000 | d13 B | d14 K* | d15 S4M | d16 B | d17 J P | d18 S12M | d19 S30M | d20 J | d21 S120M * | d22 J | d23 J | d24 S2B P | d25 B | d26 J | d27 S500M | d28 J x3 * | d29 B * | d30 J x9 *.
ME table is identical except d7 = T500K (V `monkey .../Configs/DailyLogin`). Pattern: small trophies early, alternating Speed/Spin/Boost, Special anchors at 7/14/21/28-30.

## 7. Jackpot (slot machine) (V)
`Factory_Jackpot` (`Game.Factory_Jackpot.asset`, identical numbers in ME): roll 2.25 s, start/end delay 0.25, **outcome rates NoReward 0.15 / Double 0.60 / Triple 0.25** (relative, normalized), `OriginalRateUnlockLevel=75`, `FreeSpinsPerDay=1`, `VipFreeSpinBonus=1`, `SpinIapProductId=com.speed.keyboard.slot.machine`.
`Data_Jackpot`: `_lastFreeSpinUtcDay`, `_freeSpinUsed`, `_debugFreeSpinBonus` (also the bank for earned spins via `GrantFreeSpins`, e.g. daily reward / IAP `jackpot_spin`), `_jackpotPityCount`, `_hasUnlockedOriginalRates`. Free total = daily + VIP bonus + banked.
`Jackpot_Spin.Roll`: pity - after 10 consecutive misses (`ShouldForceJackpot`) force a Triple on an item with Ranking <= Uncommon; else weighted pick by rate (uses `_rateBeforeUnlockLevel` until player Level >= 75, then `_rate`), then outcome roll; `OnlyX3` claim-type items never pay on Double. Spin consumption (`Jackpot_Spin_UI.cs`): `TryConsumeFreeSpin()`, else `IAPManager.Purchase(SpinIapProductId)` then consume. Day key = UTC ticks / day.
KT pool (17 assets; `_rate` / `_displayRate`): Common Cowboy Hat 15/15, Speed 1.5M 15, Trophy 5K 15; Uncommon Candy Armor 10, Speed 6M 10, Trophy 20K 10; Rare 100M Speed 3/6, 250K Cup 3/6; Epic Cart 5/3.5; Legendary Crown 2/3; Mythical Cracky Sword 1/2; Unique 500M Speed 0.5/1, Plane 0.5/1, Water Sound 0.5/1; Ascended 10B Trophy / 35T Speed / Rocket all `_rate` 0.0001 but `_displayRate` 0.5. **Displayed odds for Ascended are ~5000x the real rate** - store-compliance risk (V values, I judgement). ME pool swaps wearables for leaf/carrot/banana/meteorite/lava-crown items (V listing).
UI: `Jackpot_Spin_UI(_Item)`, `Jackpot_Paytable`, `Jackpot_Result_{Outfit,Speed,Trophy}`, entry `UI_Jackpot_Button`, shop tab `Shop_Jackpot_IAP_Item`.

## 8. Gacha (KT only; V `Configs/Gacha`)
`Gacha_Box_Asset{_boxName, _rewards[{_item,_weight}], _price, _prefab}`, opened via `Factory_Gacha.OpenGachaBox(config)` (single-instance guard). Price in **Gem**, deducted before the open animation; button interactable only if `Gem >= price` (V `Gacha_Box_Popup.cs`). Boxes: Green 10,000 (weights 35/25/25/10/5), Red 20,000 (35/35/20/15/5), Violet 2,000 (30/30/20/10/10). Events `Event_Gacha_Box_{Open, Open_End, Information, Stand_Selected}`; analytics `LogHelper.LogBoxGacha`.

## 9. Rarity, quests, misc
- `Ranking_Type` (V): Common0, Uncommon10, Rare20, Epic30, Legendary40, Mythical50, Unique60, Ascended70 - drives boost-shop weights, jackpot `_ranking`, pity filter. A second enum `Rarity_Type` (0-5) + `Rarity_Asset/Randomizer` exists in KT (V) - overlapping enums = tech debt (I).
- Leaderboards: `Logic/Ranking` holds only `Ranking_Type.cs` in both repos, plus `Factory_Ranking`; no leaderboard backend found (V file list; I conclusion).
- Quest (ME): `Quest_Arrow`, `Quest_Focus_Msg/Pointer`, `Quest_Zoom` are tutorial guidance, not a quest economy (V).
- Rating: `Data_Rating{RatingDone, RatingInThisSession (reset every launch), RatingCount}`; Good -> `AppStore.Review()` + done, Bad -> session flag only (V). Trigger condition not traced (I).
- Booster (KT): `Booster_Asset{type JetPack/Shoes, Addressable prefab, Duration}`; `BoosterButton` activates via rewarded ad (V).
- Assist (ME): `Assist_Asset{Carpet, fuel toggle, FuelDuration 5 s, RefuelDuration 10 s}`, `Data_Assist{Dictionary<id,Assist_Data>, Equipped}`; unlocked by carpet IAP (V). KT has `Factory_Carpet` instead.
- Announcement: `Announcement` + `Announcement_Coundown` (name typo in repo). Settings: `Settings`, `Settings_Toggle`, language items (V).
- Item (KT): `Item_Asset/Data/Manager/Inventory`, events `Event_Item_{Equipped,Locked,Unlocked}`; weapon/throw classes are combat, not economy.

## 10. Common monetization skeleton (copy for new games)
1. Wallets in one `Data_Currency` (`DataValue<double>`, per-mode dictionaries optional) + spread FX on every grant.
2. Free-grant loops: 30-day calendar daily login, free daily rewarded currency (5 x 100), 1 free spin/day (+1 VIP), restocking shop.
3. Rewarded ad wherever the player is blocked: revive, missed daily, sold-out shop, skin-with-ads, x2 earnings, rebirth/teleport skips, "+100 gems" popup.
4. Interstitials only at natural breaks (death, revive-cancel, checkpoint, popup close) plus a timed break-ads popup; gated by time/session/level/remote placement config.
5. IAP ladder starter -> mid -> whale (0.99 .. 99.99/169.99) with bonus on top tiers; remove-ads as a bundle side effect of carpet/skin packs; weekly VIP sub (no inter/banner, cup/exp multipliers, free revives, extra spin); consumable spin/boost packs; A/B price variants by id suffix.
6. Funnel popups with session caps (VIP then pack-all once per session via `Data_IAP.IsIAPInAppOpen`, NoAds after 3 inters, speed popup once).
7. Everything tuned in SO assets + remote JSON; IDs as constants in `IAPConstants`; payouts defined in the catalog, switch-handled in one receiver.

## 11. Differences KT vs ME (V unless noted)
| Area | KT | ME |
|---|---|---|
| Game | Speed/Paint Keyboard, Obby minigames, per-minigame wallets | Monkey Escape, worlds 1-4 |
| Shop | Stands (timed), Gacha, Item/weapon | Aura tab, `Boost_Fuse`, per-world equipped boosts |
| Ads | `Logic/Ads` | `Logic/Monitize`: native fullscreen/half ads, level>=10 inter gate |
| IAP | one flat slot SKU | slot ladder item1..9; map unlock 2-4; skin.pack 16.99 |
| VIP | exp x2 | exp x5 |
| Daily d7 | keycap | trophy 500K |
| `Data_Shop.cs` | 371 lines | 505 lines |
| Gacha | present | absent |
| Carpet/assist | `Factory_Carpet` | `Assist_*` with fuel |

## 12. Proposed classification

| Candidate | Class | Proposed name | Must contain |
|---|---|---|---|
| Ad call contract | RULE | `ads-wrapper-contract` | single `AdsHelper` facade, never call SDK directly; skip flags (Banner/Inter/Reward) and VIP-keeps-rewarded; rewarded `Action<bool>` + fail toast; Editor mock returns true; stable-int placement enum logged as string |
| Interstitial gating + break-ads popup | SKILL | `ads-popup-flow` (EXTEND existing) | time-start/time-between/session/level gates with 60/40 defaults; break popup (+100 reward vs close -> inter); mutual-exclusion statics with SubsystemRegistration reset; NoAds popup after 3 inters; per-site placement list |
| IAP receiver + catalog | SKILL | `unity-iap-port` (EXTEND existing) | ProductCatalog JSON as price/payout source; `IAPConstants` subtype strings; `Receive` switch; transaction-id dedupe; base vs variant id; entitlement-based restore; price-text fallback + OnProductsFetched; `Data_IAP` ownership |
| VIP subscription facade | SKILL | `subscription-vip-perks` | state-based perks from payout quantities; `OnChanged` event; refresh on resume; daily free-revive cap; remove-ads side effects; multiplier fallbacks |
| Price ladder / bonus structure | DATA | `iap-price-ladder` | table 4.1; bonus ~50% on 69.99+ tiers; consumable vs non-consumable typing; `.stand/.update` suffix semantics; per-game overrides (ME slot ladder) |
| Daily login 30-day | RECIPE | `recipe-daily-login` | Data (start UTC day, claimed flags); Factory array + frames; 4 claim states; missed-day-by-ad; reward-type enum; reward table section 6; debug advance-days |
| Jackpot slot | RECIPE | `recipe-jackpot-slot` | outcome rates .15/.60/.25; pity at 10; level-gated rate tables; free spin/day + VIP bonus + IAP spin fallback; displayed-vs-real odds compliance warning; paytable UI |
| Rotating boost shop | RECIPE | `recipe-restock-shop` | slots + UTC restock timer; weighted rank roll per world; VIP weights every Nth; stock ranges; lifetime MaxStock; IAP capacity slots; ad forced restock |
| Gacha box | RECIPE | `recipe-gacha-box` | weighted reward SO list; price in Gem deduct-then-open; popup singleton guard; events |
| Currency + spread | SKILL | `currency-spread-fx` (EXTEND existing) | grant-then-post order; `Event_Currency_Spread_Start` signature; per-currency spread SO fields; compact-number format |
| Economy reference numbers | DATA | `economy-reference-numbers` | free cup 5x100; restock 200 s / 4 slots; capacity 5(+3); gacha prices; weight tables; MoreCup 100; ad timings 60/40/60 |
| Remote config priority | RULE | `remote-config-priority` | Server > Firebase > Local > code defaults; JSON IAP variant string; per-placement override list; no hardcoded ad timings |
| Monetization analytics | RULE | `monetization-analytics-events` | LogIAPSuccess with receipt parse; ad show/complete per placement; payer flag `TotalPurchaseCount`; Editor logs only |
| Store compliance | RULE | `store-compliance-checks` | functional restore; displayed odds equal real odds; price only from store; no fake loading spinner as restore |
| Wiring audit | TOOL | `monetization-wiring-audit` | scan AdsPlacement enum vs call sites; catalog ids vs receiver subtypes vs `IAPConstants`; Factory assets assigned; button product ids exist in catalog |

Open items not traced (I): leaderboard backend, rating trigger, Common-Rare KT boost numbers, live remote ad timings, `Shop_Stand` timer durations, `Factory_Shop.GetBoostStockRange` values.
