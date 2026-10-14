# 07 - UI behavior, code layer and screen patterns (reverse-engineered)

Sources (read-only): `KT` = knife-tower-troll-unity, `ME` = monkey-escape-unity (primary); `CT` = climb-tower-unity, `BO` = obby-unity (old, layout only).
Framework code root: `KT/Library/PackageCache/com.codesketch@0fe9d8bab8cb/Runtime` (written `PKG/`). Prefab paths are relative to `Assets/_Game/Prefabs/` unless noted.
Tags: **V** = VERIFIED (read in file/YAML or counted by script), **I** = INFERRED. Counts come from a YAML scan of all `_Game` prefabs (KT 223 button GOs, ME 184).

## 0. Framework identity (user correction applied): ONE framework, three eras
| Era | Package / folder | Namespace | Used by | Install | Tag |
|---|---|---|---|---|---|
| CFramework | `Assets/CFramework` (embedded folder, no UPM) | `CFramework.*` | CT, BO | copied into Assets | V folder exists; lineage I |
| CodeSketch 0.1.1 | `com.codesketch` + `com.codesketch.installer` | `CodeSketch.*` (`.UIPopup`, `.UIView`, `.Utilities.UI`, `.Audio`) | KT, ME | manifest git URLs `https://github.com/CodeSketch-dev/CodeSketch.git#main` and `https://github.com/CodeSketch-dev/CodeSketch.Installer.git` | V (manifest, package.json) |
| SketchEngine 1.0.1 | `com.sketchengine` | `SketchEngine.*` (same type names; popup code moved to `Runtime/Core/Popup`) | break-and-steal (vibe-coded, not a reference) | manifest git URL `https://github.com/CodeSketch-dev/SketchEngine.git` | V |
- Popup / PopupManager / UIPressPrimeTween / AudioButtonSfx / UISafeArea behave identically in CodeSketch and SketchEngine (same Escape handling, stack, tween values) V. Treat as one framework with versions: resolve the namespace from the installed package, never paste code across eras. Skills that say "CodeSketch vs SketchEngine differ" should say "same framework, renamed; read the installed version".
- Two tween libs coexist: framework `Popup`/`View` sequences use **DOTween**; button press, toast, Daily/Jackpot attention loops use **PrimeTween**; game code (Currency_*) uses DOTween. V

## 1. UI code layer
### 1.1 The two scripts on ~85% of buttons (guid resolved via `.cs.meta` in the package)
| guid | Script (file) | On button GOs | Behavior (V) |
|---|---|---|---|
| `9f438e38...` | `UIPressPrimeTween` (`PKG/Utilities/UI/UIPressPrimeTween.cs`) | KT 191/223 (86%), ME 150/184 (82%) | Pointer down: scale target to `0.9` over `0.1s`, `Ease.OutQuad`, unscaled time; up/exit: back to 1. Ignored when `Button.interactable` is false. Stops tween and resets scale on disable. Fields `_target` (default self), `_scaleThreshold`, `_duration`. |
| `d0ec04dc...` | `AudioButtonSfx` (`PKG/Audio/AudioButtonSfx.cs`) | KT 188 (84%), ME 146 (79%) | Plays on **PointerDown** (not onClick): `_sfxOnClick` or default `AudioMixerFactory.SfxUIButtonClick`; skipped if not interactable. Needs a `Button` on self/children. |
- Every button = `Image + Button + UIPressPrimeTween + AudioButtonSfx` (Image 222, Button 220 of 223). Role extras: `PopupButtonOpen` (HUD buttons that open a popup, 10), `CodelessIAPButton + IAP_Purchase_Button` (41), `UI_Button` (grayscale helper), `UIPointerClick` / `UIPointerDrag` (non-Button touch areas: jump, attack, camera Look pad), `AnimationSequence` (attention loops). V
- Custom buttons derive `UIButtonBase` (`PKG/Core/UI/Button/UIButtonBase.cs`): finds the Button in children, adds the listener in `Awake`, override `Button_OnClick()`. V
- Disabled state = grayscale material swap on `Button.image` and extra images (`Factory_Config.MaterialGrayScale`), not a tint. V (`UI_Button.cs`)

### 1.2 Popup / PopupManager / View / ViewContainer
| Piece | Contract | Tag |
|---|---|---|
| `Popup : MonoCached`, requires `CanvasGroup` | Root of every popup prefab, stretch (0,0)-(1,1). `OnEnable` pushes to the `PopupManager` stack and plays the open sequence; `Close()` plays it backwards then `Destroy(gameObject)` (instantiated per open, never pooled). `interactable` false until open ends. Fields `_openDuration`, `_closeDuration`, `_ignoreTimeScale`, `_sfxOpen/_sfxClose`, `_animations[]` (SerializeReference), 4 UnityEvents. | V |
| Animation modules | `PopupAnimationBackground` (spawns a full-stretch Image+Button dim as a *sibling behind* the popup, fades 0 -> color.a, click closes), `PopupAnimationScale` (`_scaleStart 0.3 -> 1`, field default Ease.OutBack), `PopupAnimationFade` (CanvasGroup 0 -> 1). `_durationRange` (0..1 slices of open duration) staggers modules. Close = same sequence backwards, `timeScale = open/close`. | V |
| Back button | Only `Popup.Update`: `Input.GetKeyDown(Escape)` (Android Back) -> `Close()`, and only for the top popup (`PopupManager.PushToStack` calls `SetEnabled(false)` on the previous top). No other Back/Escape code in KT/ME scripts; views have none. | V |
| `PopupManager.Create(prefab)` | Static. Instantiates under the Overlay canvas that has a `PopupRootSetter` (highest sortingOrder wins), last sibling. 9 call sites in KT, all with a serialized prefab ref; HUD buttons use `PopupButtonOpen` (serialized `_popup`, zero code). Events `EventPopupOpened/Closed`, `Count`. | V |
| `PopupButtonNoThanks` | Shows a "No thanks" button after `OpenDuration + 0.5s`, scale 0 -> 1 over `0.25s` Linear. Standard on ad/revive popups. | V |
| `View` + `ViewContainer` | In-game HUD layers (`Minigame/SpeedKeyboard/SpeedKeyboard_GUI_View.prefab`). `ViewContainer` (persistent MonoSingleton) `PushAsync(AssetReference)` loads an Addressable, blocks the previous top view, opens the new one; closes all views on scene change. Prefab = `View` + `Root` child (+ `SafeArea`). | V |
| Popup vs HUD | **Popup**: instantiated on demand under the popup canvas, dim, scale-in, closes on Escape/dim click, destroyed. **HUD/View**: Addressable, one per mode, under `ViewContainer`, no dim, no Escape. | V |
- Observed (KT 32 / ME 23 popups with animations): open/close `0.1/0.1` is the mode (about 70%); big popups (`IAP/IAP_Pack_Carpet`, `Item/Item_Inventory`, `UI/Settings/Settings_Popup`) use `0.3/0.2`. `ignoreTimeScale` 0 everywhere. Dim alpha `0.94` (most), `0.86` inventory, `0.706` settings, `0.78` MoreCup_BreakAds, `0.5` debug. Scale ease `OutBack` (enum 27) in about 60%, Linear (1) in the rest. V
- 12 popups carry `PPDepthOfField_TriggerEnable` (depth-of-field post FX while open). V

### 1.3 Feedback, counters, toasts, notification, tutorial
| Item | Recipe (values read in code) |
|---|---|
| Currency count tween | `Currency_Bar`: subscribes `DataValue<double>.OnValueChanged`; `DOVirtual.Float(0,1,0.7s)` lerps the displayed value, `Ease.OutCubic`, `SetUpdate(true)`; text `BigNumber.ToCompactString()` (K/M/B). Kills tween on destroy. No `Update`. |
| Bar pulse on receive | `Currency_Bar_Spread`: scale pulse `0.05s`, `Ease.OutQuart`, `_scaleCount 8` (one per flying coin). |
| Currency fly-to (spread) | `Currency_Spread` + SO `Configs/Currency_Spread_Money.asset`: fadeIn 0.3; scale-in 0.5 with `Ease.OutBounce` (enum 30); back-step 0.5 over 0.09; `flyDelay 0.5`; `DOPath` cubic-bezier to the bar icon in `flyDuration 0.3` (controlStart (0,8), controlEnd (6,-6)); fadeOut 0.2; stagger = `sequenceDuration 0.5 / (count-1)`; optional spiral burst 0.6; end VFX `CurrencySpreadVfxEnd`. Per-currency prefab trio `CurrencyBar_X / CurrencySpreadItem_X / CurrencySpread_X` in `Currency/<Type>/`; items spawn in `UIGlobalCanvas.ContainerOverlay`. |
| Announcement banner | `Annoucement/Announcement.prefab` (sic): 800x50 strip at y +260 from center; CanvasGroup fadeIn 0.3 OutSine, hold `fadeOutDelay*2 + extra` (2s*2), fadeOut 0.3; text pulse scale 1.1 over 0.15; `PushMessage` UniTask with CancellationToken. |
| Warning toast | `UI_Notification_Warning.Show(msg, 2.5s)`: fadeIn 0.25 OutBack, blink 0.15, hold, fadeOut 0.35 InSine; ignores calls while showing; completes on `Event_Home_Return`; `ShowCountdown(pattern, sec)` variant. |
| Toast text | `UINotificationText.Push(msg)` (`PKG/NotificationText`): pool of 1; scale 0.25, fade 0.35, move Y 0.4, hold 0.5, fadeOut 0.9, all Linear; hard-coded design width 1280. |
| Notification dot | Child `Notify` 40x41, anchor top-right `(1,1)`, pos about `(-10,-6.5)`, on every HUD home button and tab (`UI/Button/UI_Button_Daily.prefab`). Plain `SetActive(bool)` from a data event (`Shop_Boost_Inventory_Button.RefreshNotification`, `Shop_All_Tab._goNotiVipSkin`). No tween, no count. |
| Attention loops (PrimeTween) | Free spin button: shake rotation Z (frequency 24) then `Delay 1.2`, repeat. Paid state: scale yoyo `InOutSine`, cycles -1. Daily "today" card: shake angle 1, 0.65s, rest 1.1s, scale x1.02; missed card scale x1.04 over 0.7s; outline alpha 1 <-> 0.2 over 0.65s InOutSine; normal card scale 0.85. |
| Reveal sequence (gacha) | name/title `DOAnchorPos` 0.5s OutBack from a 24-px top margin, lead delay 0.06; buttons scale 0 -> 1 in 0.28s OutBack, start delay 0.1, stagger 0.08. |
| Scroll-to-focus | Daily: `Tween.Custom` scroll position to today's card, `Ease.OutQuad`. |
| Loading screen | `LoadingScene` under the popup canvas (`Scripts/Logic/Scene/LoadingScreen.cs`): fade 0.25, real scene progress mapped to a target then fake fill to 100% over `_finalizeDuration 1.5s`, minimum hold at 100%. Background Image + `AspectRatioFitter`; bar 834x83 at y=250 from bottom, `Fill` 826x73. |
| Tab system | `Shop_All_Tab : UIButtonBase`: click -> `StaticBus<Event_Shop_All_TabSelected>.Post(type)`; every tab listens and swaps `Button.image.sprite` `_frameOn/_frameOff` (no tint, no tween); `Shop_All_Content` panels listen and toggle. Subscribe in `Awake`, unsubscribe in `OnDestroy`. |
| Spotlight tutorial | `Quest/Quest_Focus_Msg.prefab`: four 3500x3500 dim Images around a 325x125 hole; the `Focus` group holds 4 `Button` images that block input outside; message TMP below; hole shrinks with `DOVirtual.Float(1,0)` (OutSine). `UI_Button_Focus.LateUpdate` converts a world target to canvas position (the only per-frame UI work besides optional safe area). No hand-sprite prefab exists; pointing uses world arrow `+1Speed/Arrow.prefab`. |

### 1.4 Canvas organisation (V from `Prefabs/GameSingleton.prefab`, same in KT and ME)
| Canvas | Mode / sort | Contains | Per-frame |
|---|---|---|---|
| `Canvas` (HUD overlay) | Overlay / `2506` | `Root` -> `Notification_Warning`, `OverlayColor` (screen flash), `SafeArea` (UISafeArea), `CutSceneFocus` (letterbox bars 125 high) | none |
| `Canvas_Popup` + `UIGlobalCanvas` | Overlay / `12506` | `Root/PopupRoot` (`PopupRootSetter`), `OverlayContainer` (fly FX), `UI_Internet_Popup`, `LoadingScene`; `ViewContainer` also under this Root (I) | none |
| Per-mode `Player_GUI` | Own canvas, Overlay, sort 0 | `SafeArea` child with joystick, action buttons, fuel bars, `Look` drag pad | event-based |
| Third-party | Transition Plus 20000, Graphy 30000, ad prefabs 500/999 | | |
| World-space | only 2 (`Character.prefab` rm2; `WouldYouRather.prefab` rm2 sort 5) | name tags / quiz | |
- Whole game = 2 persistent overlay canvases (inside a persistent `GameSingleton`) + per-mode HUD canvases; almost no world-space UI. Every CanvasScaler is ScaleWithScreenSize 1920x1080, Expand (5/5 KT, 5/5 ME). Popup prefabs have **no Canvas** (inherit the popup canvas). V

### 1.5 Safe area, banner, joystick
- `UISafeArea` (`PKG/Utilities/UI/UISafeArea.cs`): `Screen.safeArea` -> anchors; `_conformX/_conformY` default true; `_refreshOnUpdate` default **false** (refreshes on enable and when screen size/orientation changes); handles Samsung NaN anchors. Placed on HUD `SafeArea` children, `ViewContainer`, `Shop_All`. V
- Banner clearance: **no code** in KT/ME (grep "banner" only hits ad gating in `AdsHelper`); banner prefabs are MAX plugin canvases (sort 500). So the 200-px bottom clearance is a layout convention, not an engine feature. V (absence)
- Joystick: Joystick Pack (`Assets/Packages Required/Joystick Pack`, Fixed/Floating/Dynamic) behind `PlayerGUI.JoystickMove`; `_fxJoystick` toggled; right half is a `Look` pad anchored `(0.5,0)-(1,1)`. Class V; exact variant I.

## 2. Localization, text, fonts, color, sprites
| Topic | Finding | Tag |
|---|---|---|
| Stack | Unity Localization 1.5.12 (KT), table `LOCALIZE` + `LOCALIZE_<code>`, 9 locales: en, vi-VN, ja-JP, ko-KR, ar-EG, ar-SA, es-MX, tr, uk-UA. RTLTMPro installed. Locale detected from `Application.systemLanguage` once and persisted (`Factory_Localize.EnsureLocaleInitialized`, waits for the async table load). | V |
| Components | `Localize_TMP_Text` (Odin key dropdown, `Factory_Localize.Get(key)`, re-applies on `SelectedLocaleChanged`), `Localize_TMP_Font` (font by locale from `Factory_Localize_Font`; material swap only with a flag), `Localize_TMP_Text_Format` (extracts `{0}` args from existing static text). Nearly every TMP has `Localize_TMP_Font`; static labels also `Localize_TMP_Text`; dynamic numbers set `.text` from code. Subscribe `Awake`, unsubscribe `OnDestroy`. | V |
| Fonts | `UTM AvoBold SDF` (225 TMPs in KT, `Fonts/Bounce`), `Nunito-Bold` (119, `Fonts/Localization/TMP`), `ChangaOne SDF` (104). Locale fonts: Nunito-Bold, Jua (ko), MPLUSRounded1c (ja), AligarhArabic (ar). | V |
| Outline presets (materials, not Outline component) | AvoBold `Outline 35 / 75 / 100` (width 0.35/0.75/1.0, black outline, black underlay offset (0.12,-1), white face) + `_Ins` instancing. ChangaOne `Outline 15/20/25/50` (+`_Instancing`, `_Instancing_Billboard` for world text; underlay y -0.79 alpha 0.82). KT usage: AvoBold 75 (92) +75_Ins (27), 100 (82), ChangaOne 25 (19), 20 billboard (20). | V |
| TMP settings | Auto-size on 80% (363/451); min `18` nearly always; max 36/40/42/50/52/72 (72 most common); overflow = Overflow; Center/Middle 88%; **Raycast Target off on 82% of TMPs** (368/451) and 38% of Images; Image type Sliced 31% (244/786), Simple 67%. | V |
| Number format | `BigNumber.ToCompactString()` (K, M, B...; `PKG/Number/BigNumber.cs`) over `DataValue<double>`. | V |
| TMP colors (KT) | white `FFFFFF` 393 (87%), gray `909090` 15, gold `F4C046` 13, orange `FFA800` 10, yellow `F3F300` 9, `FFD400` 3, lilac `9D9FCD`/`5E5D9E` 3 each, red `FF0A00`/`FF2C00`, green `48FF00`. ME same family (green `35FF00`, `FF5955`). Everything else is baked into outline materials. | V |
| Image tint | `FFFFFF` on about 97% of Images (828 of ~870): **color lives in the sprite, not the tint**; black `000000` (44) = dim/mask panels; `BFBFBF` (5) = dim overlay; one-offs `E01A1A`, `3D68C4`, `FFBD00`. | V |
| Rarity | `Rarity_Type`: Common, Uncommon, Rare, Epic, Legendary, Mythic (6). `Rarity_Asset` SO has a single `Color`; no instance assets found under `_Game`, so hex values are unrecoverable. | V enum / colors unknown |
| Sprites | Art in `Assets/_Art/2D/GUI/{_Updated,v1}` (KT 490 sprites, ME 432). Import: Sprite(2D&UI), PPU 100, mesh Tight, mipmaps off (489/490), alphaIsTransparency on, no legacy packing tag, 9-slice border on about 9% only (44/490; ME 41/432) = frames/boards/bars, default max 2048 with Android/iOS overrides (some 512/1024 compressed). Atlases `Assets/_Art/2D/Atlas_<Domain>.spriteatlasv2` + `Master.spriteatlasv2` (KT: Home, Shop, Gameplay, Character, Speed, Weapon; ME: Gameplay). | V |

## 3. Hierarchy and naming (V; scripts over KT 32 / ME 23 popups)
- Popup root = feature name (`Daily_Login_Popup`, `Gacha_Box_Popup`), `Popup` component, stretch. 94% have a child `Root` (stretch); 75% a `Board`. Canonical tree:
  `Feature_Popup (Popup, CanvasGroup)` > `Root` > optional `Scale` (fixed size = board + margin, scale-animation target, y offset +20..+75) > `Board` (sprite) > `Btn_Close` / `Title` or `Text_Title` / content (`ScrollRect`, `Layout` HLG, action `Btn_*`).
- Board sizes: 1146x754 and 1154x768-800 (large), 800x650 (settings), 665x512 (confirm), 528x435 and 525x370 (mini), 1432x743 (IAP hero). `Btn_Close` 97x93 (or 100x100) at top-right, inset about (-65..-70, -67..-70).
- Dim: spawned by `PopupAnimationBackground` (preferred) or a sibling `Background` Image (11 uses).
- Prefixes: `Btn_` (130) and legacy `Button*` (56), `Text_`/`Text` (418), `Icon` (173), `Frame` (135, state/selected outline), `Root` (116), `Content`, `Layout` (HLG of bottom buttons, 720-840 x 115), `Fill`, `State_*` (exclusive panels), `Notify`, `Cooldown` (radial fill), `Tab_<Type>`, `Item`.
- Row/card prefabs are separate files `<Feature>_Item.prefab` beside the popup; per-state variants are child objects (`BtnClaim / Missed / Today / Claimed`) toggled by SetActive; scripts named `<Feature>_<Role>`.
- **Page vs popup**: page = `Title` bar stretched top (175 high, text 200x50, `Btn_Back` 103x107 at x=98.5) + `Background` + `SafeArea` child (`Daily/Daily_Login_Popup.prefab`, `Shop/All/Shop_All.prefab`). Popup = floating Board + top-right `Btn_Close`.
- HUD home button: root 167x162 with `Frame` 155x106, `Icon` (y+100), `Notify`, `Text` (y -14.3).
- HUD anchors: bottom-right cluster anchored `(1,0)` with negative x (`Action` 232.5 at (-235,299), `BtnAttack` 197 at (-470,489), `BtnCarpet` 158 at (-124,776)); fuel/progress bars top-center (0,-150) 484x39 or (0,-87.5) 834x83; currency bar top-right (-332,-88) 286x81 (`Bar`, `Plus` 74x75, `Icon` 166x174 overlapping the left edge, `TextCount`). All inside a `SafeArea`.
- CT/BO (old): UI from the older CFramework `PopupSetting`/`ButtonSettings`; BO HUD is scene-authored. Use as ideas only; lack of `UIPressPrimeTween` there is I (not re-verified).

## 4. Screen catalog (candidates NOT in `ui-pattern-library`, which only has `skin-shop`)
Sizes in the 1920x1080 reference. All V.
| # | Screen | Prefab | Layout contract | Hooks |
|---|---|---|---|---|
| 1 | Settings | `UI/Settings/Settings_Popup.prefab` | Board 800x650; `Title` stretch top (y-66, h100); 3 toggle rows 635x80 pitch 108-112 (Music, Sound, Vibration); bottom `Layout` HLG 720x117; `Language` sub-panel stretched over Board; close 65x87; open 0.3/close 0.2, dim 0.706 | `Settings_Toggle`, `Settings_Language_Item` |
| 2 | Daily login | `Daily/Daily_Login_Popup.prefab`, `Daily_Login_Item.prefab` | Page: title bar 175 + Btn_Back; horizontal ScrollRect (0,0.5)-(1,0.5) h700 y-27, scrollbar 500x20 under; card 431x617: `Thumbnail` 235 (y+35), `Text_Title`, `Text_Value`; state children `BtnClaim`, `Today` (455x632 outline), `Missed` (+`Btn_Recovery` 325x125), `Claimed` (+`Tick` 102x79) | auto-scroll to today, today shake, home button + Notify |
| 3 | Gacha box | `Gacha/Gacha_Box_Popup.prefab`, `_Item`, reveal in HUD canvas `Gacha_Box_Information` | Board 1154x769; `Bg` 940x454 with ScrollRect inset (-214,-287); `Btn_Gacha` 347x116 y88; close 97x93. Reveal: name+title drop in, `Btn_Equip` / `Btn_NoThanks` scale in | reveal sequence, duplicate flag, rarity |
| 4 | Jackpot / slot | `Jackpot/Jackpot_Spin.prefab` (+Item, Paytable_Item) | Machine art 1413x814 (y+76); slot window 821x413 (y+146); `Spin_Free` and `ButtonIAP` 275x110 at y134 (state swap); `Btn_Table` 91x103 opens `Paytable` 286x480 left; lever `Toggle_On/Off` 133x260 right; close 135x135; result overlay `Result_Cup / Result_Speed / Result_Outfit` + `Fx_Shower` (UIParticle) | free-spin shake, paid yoyo, `Audio_Volume` |
| 5 | Rating | `Rating/RatingPopup.prefab` | `Block` full dim; board 525x370; title y-32; two buttons 210x100 at x=+-121, y-99; Good -> store review, sets `RatingDone` / `RatingInThisSession` | `RatingHelper.CanShow()` |
| 6 | Revive / result | `Result/Result_Revive_Checkpoint.prefab` (+Killed, Stage, Skip) | Scale 748x725 > Board 665x512; title top; `Text_Desc` 525x50; `Countdown` ring 147 (fill 174) center; `Btn_Revive` (ad) / `Btn_Revive_Free` 275x105 same slot y79; `Btn_NoThanks` 275x85 hanging below board (y-50), delayed | `PopupButtonNoThanks`, countdown fill |
| 7 | Mode select card | `Minigame/Minigame_Selection_Item.prefab` (+`_Large`) | Card 488x357 button; `Thumbnail` anchors (0.06,0.09)-(0.94,0.82); top `Title` strip 524x124 with `Text_Name` left (0.03-0.72) and `Status` HLG right (0.76-0.975); `Frame` overlay; `CommingSoon` full overlay | status enum |
| 8 | Side-tab shop | `Shop/All/Shop_All.prefab`, `Shop_All_Tab_Item.prefab` | Page; left `ScrollRect_Tab` 285x740 at x=5; tab 222x82 (icon 101x81 left, label, dot top-right); 6 stacked content panels (Speed, Trails, Cup, Jackpot, Offers, Sounds) toggled by tab event | tab event, red dot, sold-out sorter |
| 9 | Inventory | `Item/Item_Inventory.prefab` | Scale > Board 1154x800 (y+50); `Title` h75; ScrollRect inset (-116,-205) y-62; close 97x93; dim 0.86; 0.3/0.2 | grid items |
| 10 | IAP pack carousel | `IAP/IAP_NoAds_Popup.prefab` | No board: horizontal ScrollRect full width h631, Content = HLG + ContentSizeFitter of pack cards; close anchored to center (705,375) | `CodelessIAPButton` per card |
| 11 | Subscription / VIP pass | `IAP/IAP_Subscription_VIP_Pass.prefab` | Board 1432x743: left art 603x346, right `Title` 450x224 + `Benefits` VLG 667x382, `ButtonIAP` 525x135 bottom-right; close 100x100 | `IAP_VIP_Pass_BenefitText` |
| 12 | World / teleport list (ME) | `Minigames/Monkey Escape/World/ME_World_Popup.prefab`, `Teleport/ME_Teleport_Popup.prefab` | Board 1146x754 (y+22); title 700x90 (y-68); vertical ScrollRect inset (-79,-188) + 15-px scrollbar; close 97x93 | lock states |
| 13 | Rebirth / prestige (ME) | `Minigames/Monkey Escape/MonkeyEscape_Rebirth_Popup.prefab` | Board 1146x754 in `Scale`; `Before`/`After` cards 242x178 at x=+-229,y110; `Swap` arrow 149x135; `Progression` bar 834x83 y-108; bottom `Layout` HLG 840x115 | |
| 14 | Small ad-reward | `Currency/Currency_MoreCup.prefab` | Board 528x435; `Icon` 262x211; `Title`; `Layout` HLG row; `BtnGet` 200x80 (y67); close 100x100 | rewarded ad |
| 15 | Internet / error | `GameSingleton.prefab` `UI_Internet_Popup` | Board 1146x754 + `Frame` 925x440; `Btn_TryAgain` 285x110 y-290; `State_Reconnecting` / `State_Warning` | `UI_Internet_Manager` |
| 16 | Boost shop / item button | `Shop/Boost/Shop_Boost_Popup.prefab`, `Shop_Boost_Purchase*` | grid + purchase sub-popup; HUD entry `UI_Button_Item` 130x93 (Icon, Notify, Text) | `Shop_Boost_Inventory_Button` |
| 17 | HUD mode view | `Minigame/SpeedKeyboard/SpeedKeyboard_GUI_View.prefab` | `Level_Progression` top-center (0,-87.5) 834x83 + Fill 826x73; right column `Btn_SpeedBoost` 155x160 at (-235,-400) with 3 TMP (title above, label, timer); left `UI_Button_Item` (96,-450) | `View`, `UIHidden` |
| 18 | Spotlight tutorial | `Quest/Quest_Focus_Msg.prefab`, `Quest_Focus_Pointer.prefab` | see 1.3 | |
| 19 | Banner / toast | `Annoucement/Announcement.prefab`, `UI/UINotificationText.prefab` | see 1.3 | |
| 20 | Letterbox / screen flash | `GameSingleton` `CutSceneFocus`, `OverlayColor` | bars 125 high; stretch Image alpha tween | `UI_Overlay_*` |
| 21 | Loading screen | `GameSingleton` `LoadingScene` | see 1.3 | |
- Not found in any of the 4 projects (prefab-name search, I): pause menu, leaderboard, battle pass, friends, quest list, wheel (Jackpot covers the slot idea). Do not invent contracts for them from this catalog.

## 5. Gaps in current skills (V by reading `skills/ui-*`)
- `ui-pattern-library` documents 1 pattern; about 13 more are above. `ui-popup-from-demo` / `ui-style-rules` do not state: Escape stack, mandatory `UIPressPrimeTween` + `AudioButtonSfx`, popup `Root/Scale/Board` tree, animation module values, `Notify` dot spec, Localize components, outline material presets, dim alpha table.
- `mobile-hud-layout` has no concrete anchor examples for the bottom-right cluster or the popup/HUD canvas split.

## Proposed classification
| Candidate | Type | Proposed skill / target | Must-haves |
|---|---|---|---|
| Button anatomy: Image + Button + UIPressPrimeTween + AudioButtonSfx | RULE | `ui-style-rules` | 1. both scripts on every button; 2. press scale 0.9 / 0.1s OutQuad unscaled; 3. sfx on PointerDown, default sfx from AudioMixerFactory; 4. disabled = grayscale material, not tint; 5. search installed package before writing a press script |
| Popup prefab tree + animation modules + durations | SKILL | `ui-popup-anatomy` (or fold into `ui-popup-from-demo`) | 1. Popup(CanvasGroup) > Root > Scale > Board > Btn_Close; 2. Background + Scale(0.3 -> 1, OutBack) modules; 3. 0.1/0.1 default, 0.3/0.2 large; 4. dim alpha 0.94 default; 5. no Canvas on popup, open via `PopupManager.Create` / `PopupButtonOpen`; 6. destroy on close, no pooling |
| Back button / popup stack | RULE | `ui-popup-anatomy` | 1. Escape closes top popup only; 2. no per-screen Back handlers; 3. views have no back; 4. lower popups disabled while top open |
| Canvas organisation | RULE | `unity-ui` | 1. persistent HUD canvas + popup canvas in a GameSingleton; 2. keep sort order HUD < popup < transition < debug; 3. `PopupRootSetter` marks popup root; 4. OverlayContainer for fly FX; 5. scaler 1920x1080 Expand; 6. world-space UI only for tags |
| Page vs popup distinction | RULE | `unity-ui` | 1. page = title bar 175 + Btn_Back + SafeArea + Background; 2. popup = Board + Btn_Close; 3. tabbed/scrolling content = page, confirmations = popup |
| HUD cluster anchors and bar placement | RECIPE | `mobile-hud-layout` | 1. action cluster anchored (1,0) negative x; 2. bars top-center y -87..-150; 3. currency bar top-right; 4. everything in SafeArea; 5. Look pad = right half drag area |
| Notification dot | RECIPE | `ui-style-rules` | 1. child `Notify` 40x41 at top-right (-10,-6.5); 2. SetActive from a data event; 3. no count, no tween; 4. same on tabs |
| Tab system via StaticBus event | RECIPE | `ui-scroll-board` or new `ui-tabs` | 1. tabs post `Event_X_TabSelected`; 2. tabs and content both listen; 3. swap on/off frame sprite; 4. tab 222x82, strip 285 wide; 5. paired Subscribe/Unsubscribe |
| Currency HUD: count tween + fly-to | RECIPE | `currency-spread-fx` (verify numbers) | 1. count tween 0.7s OutCubic unscaled; 2. spread config SO (fadeIn .3, scale .5 OutBounce, fly .3 bezier, delay .5); 3. bar pulse 0.05 x8; 4. per-currency prefab trio; 5. compact K/M/B text |
| Toast / announcement / warning | RECIPE | new `ui-feedback-toasts` | 1. announcement fade .3 / hold 4s / fade .3 + 1.1 pulse; 2. warning OutBack in, InSine out, single-instance guard; 3. static `Push`; 4. cancel previous with a token; 5. text via Localize |
| Attention loops (shake / yoyo / outline pulse) | RECIPE | `game-feel-polish` | 1. shake Z freq 24 then 1.1s rest; 2. scale yoyo InOutSine; 3. stop on disable; 4. primary CTA only |
| Localization setup | SKILL | new `ui-localization` | 1. Localize_TMP_Text + Localize_TMP_Font on every TMP; 2. dynamic numbers set by code; 3. per-locale fonts incl. ar/ja/ko; 4. RTLTMPro for Arabic; 5. detect system language once and persist; 6. no baked English |
| TMP presets (font, outline material, autosize, raycast) | RULE | `ui-style-rules` | 1. outline via material (AvoBold 35/75/100, ChangaOne 15-50), not component; 2. instancing/billboard variant for world text; 3. autosize min 18, max by role; 4. Raycast Target off on non-interactive TMP/Image; 5. white face, color only for state words |
| Palette: white tint + baked sprite color + TMP accents | DATA | `ui-pattern-library/theme/theme.template.md` | 1. Image tint white; 2. TMP accents gold F4C046, orange FFA800, yellow F3F300, gray 909090, red FF2C00, green 48FF00; 3. dim black; 4. rarity 6 tiers, one hex each per game |
| Sprite import and atlas conventions | RULE | `unity-project-bootstrap` / `mobile-perf-audit` | 1. Sprite(2D&UI), PPU 100, mipmaps off; 2. 9-slice only for frames/boards/bars; 3. one atlas per domain + Master; 4. no legacy packing tag; 5. platform overrides for big art |
| Screen catalog rows 1-17 | DATA | `ui-pattern-library/patterns/<name>` (settings, daily-login, gacha, jackpot, rating, revive, mode-select-card, side-tab-shop, inventory, iap-carousel, subscription, list-popup, rebirth) | per pattern: regions with sizes, states as child objects, event hooks, variants; reuse section 4 rows |
| Safe area / banner clearance | RULE | `unity-ui` | 1. search for existing `UISafeArea` first; 2. refresh only on size change; 3. banner clearance = layout margin only |
| Loading screen / spotlight tutorial / letterbox | TOOL | `editor-tool-authoring` builders | 1. loading: fake-fill finalize 1.5s; 2. spotlight: 4 masks + hole; 3. world-to-canvas follow via LateUpdate; 4. cinematic bars 125 |
| Framework identity (one framework, 3 eras) | RULE | `unity-project-bootstrap`, `project-context-map`, AGENTS.md | 1. detect `com.codesketch` / `com.sketchengine` / `Assets/CFramework`; 2. same type names, different namespaces; 3. installed via git URL in manifest; 4. never copy code between eras |
