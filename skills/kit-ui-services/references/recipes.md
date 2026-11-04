# UI service recipes (A-J)
Sample code is illustrative: verify signatures in the installed SketchEngine package. Reference-project identifiers are provenance only.

Wording is SketchEngine-first (namespaces from the installed `com.sketchengine`); KT-version names appear only as provenance. Sample code is illustrative: check the exact signatures in the installed package before use.

### Recipe A - Popup system: prefab + Factory facade + open button
Fits: idle/tycoon (shop, offline reward), collector/throwing-pets (hatch popup), runner (revive), obby, survival, any.
Bring: `Popup` prefab skeleton (root stretch + `CanvasGroup` + `Popup` with Background + Scale animations), `PopupRootSetter` on the popup canvas, `PopupButtonOpen`, a `ScriptableObjectSingleton` Factory holding the prefab references.
Wire: popup canvas gets `PopupRootSetter` (`PopupManager.Root` finds it); root `CanvasGroup`; `Popup._animations`: Background alpha 0.7-0.94 + Scale 0.3 -> 1 (ease out-back); close button `onClick -> Popup.Close`.
```csharp
// Factory asset: Assets/_Game/Configs/... (ScriptableObjectSingleton)
public class Factory_Shop : ScriptableObjectSingleton<Factory_Shop> // namespace SketchEngine.SO
{
    [SerializeField] GameObject _shopPopup;
    public static Popup Show(Shop_Type tab)               // static facade: callable from anywhere
    {
        if (Shop_Popup.HasInstance) { StaticBus<Event_Shop_TabSelected>.Post(new(tab)); return null; }
        var popup = PopupManager.Create(Instance._shopPopup);   // SketchEngine.UIPopup
        StaticBus<Event_Shop_TabSelected>.Post(new(tab));
        return popup;
    }
}
public class Shop_Popup : MonoSingleton<Shop_Popup> { protected override bool PersistAcrossScenes => false; }
```
Why/what not to change: facade + singleton guard prevent double-open; keep prefab refs in the Factory asset, never `Resources.Load`. Pitfall: `Popup.OnEnable` plays the open sequence, so keep inactive children inactive until data is ready.

### Recipe B - Currency bar + reward fly-in
Fits: idle/tycoon (cash, gems), collector/throwing-pets (coins, eggs), runner (coins/distance reward), obby (stage reward), any with a soft currency.
Bring: `CurrencyBar_X` (bar pill `bg_number` + icon + count + plus + `ButtonShop`), `Currency_Bar`, `Currency_Bar_Spread`, `CurrencySpread_X` + `CurrencySpreadItem_X` + `CurrencySpreadVfxEnd`, `Currency_Spread`, `Currency_Spread_Config` SO (+ `Event_Currency_Spread_Start/End`), sprites `bg_number.png`, `btn_plus.png` (refs).
Wire: bar `_Type`; `Currency_Bar_Spread._spreadPrefab`; config SO fields (control points, fly duration, `flyCurve`, `vfxEnd`, `sfxEnd`); ONE bar prefab reused in HUD + shop + popups.
```csharp
// grant: change data first, then play the fly-in; the bar snaps to value-amount and counts up on arrival
Data_Currency.Get(Currency_Type.Gem).Value += amount;                 // KT names; a DataValue<double> (SketchEngine.Data) in the target
StaticBus<Event_Currency_Spread_Start>.Post(new Event_Currency_Spread_Start(
    Currency_Type.Gem, amount, rewardIcon.position, useBackground: false,
    mode: Currency_Spread_Mode.Preset, startIsWorldPos: false));
// world-space source (chest, pet, enemy): startIsWorldPos: true, start = worldPosition
```
Why: data and presentation are separated by the event; `reachEndDelay` syncs the count-up with the first arrival. Do not set the label text manually. Pitfall: the bar must exist in the active scene hierarchy (`activeInHierarchy` guard) - if it is hidden the event is ignored; the bar number uses a compact formatter (KT `BigNumber.ToCompactString`).

### Recipe C - Tutorial guidance trio (hand pointer, message hole, ground arrow)
Fits: tycoon (buy first upgrade), collector (hatch first egg), runner (tap to jump), obby (walk to checkpoint), any first-time-user flow.
Bring: `Quest_Focus_Pointer`, `Quest_Focus_Msg` (+ `Hand.png`), `Quest_Arrow` + `QuestTargetArrowGuide` + `M_Quest_Arrow` + "Animated Shader" + `T_Arrow.png`; steps persisted in a `DataValue<int> TutorialPhase`.
Wire: both focus prefabs under a persistent overlay container ABOVE popups and BELOW the loading fade (and above banner/native zones); arrow prefab in the persistent root with `Root` inactive.
```csharp
// UI step: highlight a real button, let the player's tap through
Quest_Focus_Pointer.Focus(new Quest_Focus_Pointer.FocusOptions { /* fields: see A6 section 3 (focusMode ScreenTarget, target rect, message, click-through) */ });
// world step: walk to a place; follow the player; finish on the real action
QuestTargetArrowGuide.PointTo(player.transform, target, reachThreshold: 2f, useLowestY: false,
    onReached: () => phase.Value++, stopOnReach: false);
// ... step ends / popup opens:
QuestTargetArrowGuide.Hide(); Quest_Focus_Pointer.StopFocus(callEvent: false);
```
Why: each tool does one job (UI tap / world point / navigation). Do not drive tutorial text from code strings (localize), persist the phase so a kill-and-resume continues. Pitfalls: arrow `onReached` repeats per frame (latch it); overlays (banner/native) must not cover the message; texture Wrap Mode = Repeat for the arrow.

### Recipe D - Toast and pooled floating text
Fits: all genres (idle numbers, pickup +1, damage numbers, "ad failed" messages).
Bring: `UINotificationText` prefab (+ factory reference), `Text_Money`/`Text_Speed` + `Text_Spread` + `PoolPrefabConfig` assets + the billboard instancing outline material.
```csharp
UINotificationText.Push("Watch ad failed");                         // SketchEngine.Notifications, 1-slot replace
var t = PoolPrefabGlobal.Get<Text_Spread>(Factory_Text.MoneyPool);   // SketchEngine.Patterns.Pool
t.Show("+25", hitPoint);                                             // random cone drift, scale-out, auto release
```
Why: toast = 1 slot so messages never stack; world numbers are 3D TMP with an instancing material (cheap) and pooled. Pitfall: keep all message strings in one static class + localization keys (`GameConstants.Msg*` pattern).

### Recipe E - Tabbed shop with event-selected pages + IAP cards
Fits: idle/tycoon (boosts, packs), collector/throwing-pets (egg/pet packs, gems), runner (skins, coin packs), any F2P game with IAP.
Bring: `Shop_All` skeleton (title + SafeArea + tab strip `ScrollRect_Tab` + content panels), `Shop_All_Tab_Item`, `Shop_All_Tab`, `Shop_All_Content`, `IAP_Pack_Cup_7` (template card), `IAP_Purchase_Button`, `IAP_Pack_UI_Updater`, `IAPCatalog` (ids, fallback prices, payouts), sold-out sorter.
Wire: each page root has `Shop_All_Content{_root,_type}`; each tab `Shop_All_Tab{_type, frameOn/Off}`; card `ButtonIAP` with the store's product id; payout values read from the catalog.
```csharp
public class Shop_All_Tab : UIButtonBase                     // SketchEngine.Core.UI
{
    [SerializeField] Shop_Type _type; [SerializeField] Sprite _on, _off;
    void Awake() { StaticBus<Event_Shop_TabSelected>.Subscribe(OnTab); }
    void OnDestroy() { StaticBus<Event_Shop_TabSelected>.Unsubscribe(OnTab); }
    void OnTab(Event_Shop_TabSelected e) => Button.image.sprite = e.Type == _type ? _on : _off;
    public override void Button_OnClick() { base.Button_OnClick(); StaticBus<Event_Shop_TabSelected>.Post(new(_type)); }
}
```
Why: add a tab = add a tab item + a page; "not enough currency" anywhere calls `Factory_Shop.Show(Shop_Type.Gems)`. Never store price/amount in prefab text; show the catalog fallback price until the store answers; sort sold-out items last. Add a parental gate in front of purchases (studio rule; the reference has none). Pitfall: do not build one 900-line prefab: nest one prefab per tab.

### Recipe F - Continue/revive offer
Fits: runner (crash), obby/tower (fall), survivor/boss (death), collector with timed run, any game with a fail state.
Bring: `Result_Revive_Checkpoint` shell (Board, title, countdown ring `circle1/2` (Filled), accept button with ads icon, `Btn_NoThanks` with the 1.25 s pop-in), `Popup`.
```csharp
public class Revive_Popup : MonoSingleton<Revive_Popup>
{
    [SerializeField] Image _ring; [SerializeField] TextMeshProUGUI _txt; [SerializeField] int _seconds = 10;
    Sequence _seq;                                              // PrimeTween
    void Start() {
        StaticBus<Event_Player_InputEnable>.Post(new(false));   // freeze input while open
        _seq = Sequence.Create(Tween.Custom(_seconds, 0, _seconds, v => { _txt.text = Mathf.CeilToInt(v).ToString(); _ring.fillAmount = v / _seconds; }))
            .OnComplete(GiveUp);
    }
    public void Accept() { _seq.Stop(); AdService.ShowRewarded(ok => { if (ok) Close(Revive); else { UINotificationText.Push("Ad failed"); ResumeCountdown(); } }); }
    void GiveUp() { Close(() => StaticBus<Event_Player_GaveUp>.Post(new())); }   // X, back and timeout all call GiveUp
    void Close(System.Action afterClose) { var p = GetComponent<Popup>(); p.OnCloseEnd.AddListener(() => { StaticBus<Event_Player_InputEnable>.Post(new(true)); afterClose(); }); p.Close(); }
}
```
Why: input is frozen while the offer is open; timeout, X and decline are one code path; a currency alternative (pay N instead of ad) and a subscription bypass are extra buttons. Do not hard-code a switch per game mode (KT's `Minigame_Static.Type` switch is its maintenance cost): inject outcomes through events. Pitfall: if the ad fails, resume the countdown and toast (KT behaviour).

### Recipe G - Retention bundle (settings, daily login, rating)
Fits: all mobile genres (idle/tycoon especially).
Bring: `Settings_Popup` (+ `Settings_Toggle`, language list + item), `Daily_Login_Popup` + `Daily_Login_Item` + `Factory_DailyLogin` + `Daily_Login_Asset`, `RatingPopup` + `RatingHelper`.
```csharp
// Rating policy (KT RatingHelper.CanShow): ask only after the tutorial, once per session, never after a 5-star
public static bool CanShow() => !Data_Rating.Done.Value && !Data_Rating.AskedThisSession.Value && Data_Tutorial.Completed.Value;
// call at positive moments: tutorial end, big win, after a revive popup closes
if (RatingHelper.CanShow()) PopupManager.Create(Factory_Prefab.RatingPopup);
```
Daily: `BuildItems()` from the `Daily_Login_Asset[]` in the factory (one item prefab, frame sprite by day type), `Today` claim directly, `Missed` claim after a rewarded ad; fire a `StateChanged` event so the HUD button dot/shake updates. Why: good = system review prompt + never ask again; bad = no store redirect, do not ask again this session. Pitfall: simulate days in the editor (debug keys) and test the timezone/UTC day boundary.

### Recipe H - Dev cheat menu
Fits: all. Bring `DebugPopup` (Grid 150x150 of one-action buttons) + one tiny script per action; open it from a hidden gesture or SRDebugger close. Add a cheat for each new system (currency, unlock all, skip tutorial, simulate day, toggle ads). Strip the Factory reference in release builds (`#if DEVELOPMENT_BUILD || UNITY_EDITOR`).

### Recipe I (OPTIONAL modules) - Jackpot slot and Gacha box
Fits: casual/idle and collector/hatching games only (loot-box regulation: show odds as KT does with `Text_Probability`). Jackpot: bring `Jackpot_Spin` + `Jackpot_Spin_Item` + `Jackpot_Paytable*`, the Simple Scroll-Snap asset, UIParticle FX; rates and pity live in a Factory (no-reward 0.15 / double 0.60 / triple 0.25, pity 10, 1 free spin per day + VIP bonus). Gacha: `Gacha_Box_Asset` (weighted `RollItem`), `Gacha_Box_Popup`, stand for world contact. Always include a pity counter.

### Recipe J - Pathfinding link prefab (NavMesh bots)
Fits: obby/tower/survival with bots, collector with roaming NPC. Bring `Nav_TraversalLink` (NavMeshLink + start/end children + snap-to-ground context menu); set the ground layer mask for your project; place links in map chunks so bots can cross gaps/ladders. A* variant only if the A* package is used.
