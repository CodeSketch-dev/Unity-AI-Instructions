# 16 - Economy loops and the auto-balance harness

Goal: an agent receives a GDD with loops (simulator, tycoon, idle clicker, rebirth, pet gacha, upgrades, shops, daily rewards, ads), builds the data tables, then runs a closed loop - simulate, measure, adjust config, re-simulate - until targets are met or an iteration cap is hit. Numbers (prices, odds, rates) are the designer's or agent's choice per game; this document adds no store-policy rules.

Read-only research. Nothing here was run in Unity (the `ai-game-developer` MCP was ECONNREFUSED in this session). Tags: **V** = read in the cited file, **I** = inferred or proposed.
Roots: TBE = `C:\Unity\GitProject\thunder-break-egg\break-and-steal-unity\Assets\_Game`; KT = `knife-tower\knife-tower-troll-unity\Assets\_Game`; ME = `monkey-escape\monkey-escape-unity\Assets\_Game`; RAP = `ride-a-pet\Assets\_Game`; SAE = `steal-an-egg\Assets\_ROOT`; CT = `climb-and-jump-tower\climb-tower-unity\Assets\_Game` (Bubble Gum Simulator clone). Existing tools: `skills/economy-progression-design/scripts/simulate_economy.py`, `skills/playmode-script-testing`, `skills/debug-cheats-menu`.

## 1. Catalogue of economy loop archetypes (real formulas and numbers)

### 1.1 Geometric upgrade price: `base * growth^level`
| Where | Formula | Asset numbers | Tag |
|---|---|---|---|
| KT `Scripts/Factory/Factory_PaintKeyboard.cs:126,164,182,223` | roll size and worker speed: `base * (1+g)^(level-1)` (additive growth rate g); roll speed and worker purchase: `base * g^n` (multiplicative) | asset `Game.Factory_PaintKeyboard.asset`: worker speed base 450, g=1.2 (price x2.2/level); roll size base 450, g=0.6 (x1.6); roll speed base 10000, x1.75; worker base 500, x1.86 per owned worker | V |
| KT same file | **code defaults differ from the live asset**: worker speed g 0.15, roll size g 0.15, roll speed base 10M x1.5, worker x1.2 | the asset wins at runtime, so a simulator that reads code defaults is wrong | V |
| RAP `Scripts/CoreGame/Map/HatchLuck/SO_RanchHatch.cs` | polynomial, not geometric: `ceil(basePrice * (level+1)^exponent)`; luck +1 per buy, +5 on every 5th buy (`bonusEvery`, `bonusLuck`) | asset: basePrice 5, exponent 2 | V |
| TBE `Scripts/Logic/Egg/EggBalanceFormula.cs` | pickaxe: 15 hand-tuned prices snapped by `RoundNice` (mantissa ladder 1/1.2/1.5/2/2.5/3/4/5/6/8); power x4 per tier (1,4,15,60,250,1K...250M) | prices 0,200,1K,5K,25K,120K,620K,3.1M,16M,78M,390M,2B,9.8B,49B,240B; header comment `PRICE_GROWTH = 2.05` | V |
| TBE same | extra bag slot `500 * 3^bought` | | V |
| KT `Factory_SpeedKeyboard.cs:288-318` | points to next level: piecewise `100 * 1.147^lv`, growth switches to x1.07 from level 121 and x1.12 from level 421 (`_levelPointCurves`) | asset `Game.Factory_SpeedKeyboard.asset` | V |
| ME `Data/Data_Shop.cs:116` | boost fuse: `round(BoostValue * (3 * FuseStatRetention)^Star)` | | V |
| Guideline in skill | growth 1.07-1.15 stackable upgrades, 1.5-3 per tier purchases; waits under ~5 min until a wall | `skills/economy-progression-design/SKILL.md` | V |

Pattern: authored growth rates live as serialized floats on a Factory singleton (KT) or on an SO (RAP); TBE keeps tables in a static class and bakes them to assets with an Editor generator.

### 1.2 Hand-authored price ladders
- TBE treadmill: money levels 1..11 gain 1,2,3,5,8,12,20,30,50,80,120 per step; price Free,1K,15K,200K,3M,40M,500M,7B,100B,1.5T,20T (V spec `docs/superpowers/specs/2026-10-13-treadmill-monetization-balance-design.md`); the code table `TREADMILL_PRICE` goes further (levels 12-15 legacy, 1e14..2e15) (V `EggBalanceFormula.cs`). Price rule written in the code comment: "about 7 minutes of the income a player has when the matching zone opens" (V).
- TBE zones (11): required speed 1, 1K, 7K, 50K, 750K, 12M, 150M, 1B, 5B, 25B, 100B; common-pet income 1, 6, 39, 240, 1.5K, 9.5K, 60K, 370K, 2.3M, 15M, 100M; recommended speed = required x1.15 (V `EggBalanceFormula.cs`). Cage prices 5K..8T..5e16 (the simulator array, see 2.3). Trail multipliers x2..x10000 (V `Balance_UpgradeLoopSimulation.cs`).
- IAP price ladder and shop restock weights: see `05-economy-monetization.md` sections 3-4 (cup packs 0.99..169.99, speed packs, slot ladder 0.99..8.99).

### 1.3 Rebirth / prestige
| Where | Requirement | Reward | Tag |
|---|---|---|---|
| KT Paint Keyboard (`Factory_PaintKeyboard.cs:211,217-223`) | `250K * 4.5^rebirthLevel` (asset; code default 600M x1.5) | money multiplier `1 + 1*level`; +2 free workers per rebirth; worker purchase cap `5 + 5*level` | V |
| KT Speed Keyboard (`Factory_SpeedKeyboard.cs:172-185`) | level thresholds | multiplier table from the asset (decoded): 2,4,6,8,10,15,25,40,60,80,100,120,140,160,180,200,250,300,350,400,450,500,550,600,650,700 for rebirth 1..26, then +1 per extra rebirth | V (hex decoded with `py`) |
| RAP `CoreGame/Rebirth/SO_Rebirth.cs`, `Configs/Rebirth/SO_Rebirth.asset` | 3 levels, each `payType` Money/Ads/IAP plus a required pet: 100, 1k, 10k | `GetMultiplier(n) = n + 1` (x1 at 0); applies to pet income (`RanchPetManager.IncomeMultiplier`) | V |
| KT/ME IAP | `rebirth1` 0.99, ME `rebirth2` 1.99 consumable "rebirth skip" | | V (doc 05) |
Rebirth also resets a purchase counter but raises a cap (KT worker cap) - a "permanent cap, temporary count" design that the simulator must model as state reset plus parameter lift.

### 1.4 Offline income
SAE `PetIncomeManager.cs:18-22,108-137`: cap 6 h, minimum 60 s, offline multiplier 0.15 of live income, only the first tick after cold start counts, gain goes to `DataMoney.PendingOffline`, claim popup has a rewarded x2 (`OfflineEarningPopup._adsMultiplier = 2`) (V). The standard skill says cap 2-8 h at reduced rate (V `economy-progression-design`).

### 1.5 Gacha, luck, pity
- Weighted egg list, weights validated to 100 in an SO context menu (CT `Pets/Gacha/EggSO.cs`, `EggHatchingGameLogic.SelectRandomPet`: cumulative roll in [0,100)) (V). KT gem boxes Green 10,000 / Red 20,000 / Violet 2,000 with weights 35/25/25/10/5, 35/35/20/15/5, 30/30/20/10/10 (V doc 05).
- Pity: KT jackpot forces a Triple after 10 misses; outcome rates 0.15/0.60/0.25 (V doc 05).
- TBE luck: 14 luck values 1..1,000,000 with weights 45,25,14,7,4,2.5,1.3,0.7,0.3,0.12,0.05,0.02,0.005,0.001; lean `1 + 0.08*rarity`; only 2 rarity steps affect income; size bonus `1 + 0.12*log2(luck)` capped 3.2; mutation odds Normal 88 / Gold 9 / Diamond 2.5 / Rainbow 0.5, luck up to x3 (V `EggBalanceFormula.cs`).
- TBE rarity: hits to break 4,6,9,14,20,28,40,56,80,112; spawn weights 40,25,15,10,6,3,1,0.6,0.3,0.12; income multipliers 1,2.5,6,16,39,98,240,610,1600,4200 (about x2.5 per rank, rewritten from x4-8 after the failure in section 2) (V).
- Pet income = `zone base * rarity * size * mutation`; cage multiplier `1 + 0.08*s + 0.006*s^2` for s = level-1, cap 2.4 at level 11; sell price = income x20; pet index reward = income x5 (V).

### 1.6 Ad, daily and free-grant loops
- Rewarded multipliers: offline x2 (SAE), free cup 5/day x 100, "+100 gems" popup, rebirth skip, rewarded treadmill unlocks at 2 and 5 grants (TBE spec above), luck steps where break-ads give twice the normal step (`Factory_PaintKeyboard._rollLuckRewardStep`, break = x2) (V).
- Interstitial pacing: 60 s start, 40 s between, break-ads interval 60 s (doc 05 5.2, V).
- Daily: 30-day table (small trophies early, Special anchors at 7/14/21/28-30), missed day recoverable by rewarded ad (doc 05 section 6, V); CT keeps a `DailyRewardManager` with a 1..N day cycle and `Claimable/Missed/Locked` states (V).
- Free daily jackpot spin 1 (+1 VIP), restock timer 200 s / 4 slots (doc 05, V).

### 1.7 Money formatting and number scale
`double` currencies with compact strings (K..Dc); SAE `MoneyFormat` suffixes up to `Dc` (1e33) and clamps the tier index (V); RAP `NumberHepler.TryParseAbbreviated`; KT `UtilsNumber.ParseCompactNumber`. CT stores buffs as `int` (`PetBuffData.buffValue`, `Multiply` does `value * buffValue`) - an overflow risk at idle scale (V `Pets/PetSO.cs`, I for the risk).

## 2. thunder-break-egg: "one loop-based balance" and the 165-year curve

### 2.1 What happened (V `docs/balance/balance-sim-notes.md`)
- First formula set: 8 slots, expected rarity multiplier about 6.94x, zone 11 common income 72,000/s, cage multiplier 2.4x gives about 9.6M/s; Cage 11 priced 5e16 means about **165 years**. Tuning the cage price alone was rejected; the fix was a coupled change (rarity jumps, cage multiplier cap, treadmill/pickaxe curves).
- Rebalance V2: readable rarity jumps up to 8192x for the 8th species; late cage prices 5e12 / 1e13 / 5e14; cage multiplier capped 2.4; pickaxe growth 2.05; zone speed monotonic; measured luck-size/mutation uplift about 2.25x gives Cage 11 payback about 7.6 days, inside the requested 7-10.5 day band.
- Doc rule that came out of it: "Balance is ONE loop (speed, boss, pickaxe, egg HP, pet income, cage, ads, IAP); copy relationships, not absolute numbers" (V doc 11 section 6 rule 11; `skills/economy-progression-design` "Balance the whole loop").
- Deterministic source: `Logic/Egg/EggBalanceFormula.cs` (206 lines, V). Spec `2026-10-12-balance-system-design.md` states acceptance bands: first pet 30-90 s, first cage/treadmill upgrade 2-7 min, first new biome 8-15 min, common egg break 1.5-3.5 s, rare 2-6 s, normal player survives 8/10 routes, no single luck/mutation/ad/IAP multiplier bypasses several gates (V).
- Editor audits (V, `Scripts/Editor/Egg/`): `Balance_FullGameAudit.cs` (54 lines), `Balance_RouteAudit.cs` (41), `Balance_ProgressionSimulation.cs` (60, archetypes new/normal/skilled/rewarded with session multipliers 0.65/1/1.2/1.1 and survival 0.72/0.88/0.96/0.93), `Balance_UpgradeLoopSimulation.cs` (126, greedy "buy cheapest useful upgrade" loop, 0.378 s hit interval). Menu entries `Game/Balance/Run ...` print CSV to the Console.

### 2.2 QA validity rules (V, doc 11 section 6-7, `balance-sim-notes.md`, `skills/economy-progression-design`)
1. `normal duration = QA duration / timeScale`. Verdicts only at timeScale 1; QA at 60x gave false negatives (pet lifetime 0.7 s real). Restore `Time.timeScale = 1` in `finally`/teardown.
2. Progression claims need a **clean save**; a polluted save (money 1.27M, Cage 11 unlocked) is valid only for smoke checks. The fresh-save run showed the route harness broke 61 eggs but collected no pets, so it was not a valid duration test.
3. Measure constants before modelling: a provisional 0.22 s hit cadence falsely reported near-zero boss exposure; measured clip 0.5667 s / DigSpeed 1.5 gives 0.378 s.
4. Temporary test constants (`MAX_MOVE_SPEED = 203`) must carry a revert owner.
5. Back up the dev save before mock purchases and restore after.
6. A balance change is accepted only when the runtime sample AND the normalized simulation agree.

### 2.3 What the TBE tooling still got wrong (drift evidence, V)
- `Balance_UpgradeLoopSimulation.cs` hard-codes `CAGE_PRICES` (last entry `50000000000000000` = 5e16) while the notes say Cage 11 was retuned to 5e14; it also hard-codes `TRAIL_PRICES`, `TRAIL_MULTIPLIERS`, `ROUTE_OUTBOUND` and `EXPECTED_PET_FACTOR = 25`, while `Balance_ProgressionSimulation.cs` uses a bounded uplift of `1.7` and the notes use `2.25` - three different pet factors in one project.
- The notes record a stale rarity EV `97.388`, and the plan's Task 5 had to add tests that reject it (V plan `2026-10-13-treadmill-monetization-balance.md`).
- The spec says rewarded treadmill unlocks need 2 and 5 grants and money machines stay sufficient; neither is checked by any automated acceptance - the audits only print CSV, they do not assert bands (I from the file contents: no `Assert`/threshold in the four balance files).
- Remaining open items in the notes: slot occupancy and first-pet timing are assumptions, "spend-vs-farm" decisions not modelled, full end-to-end completion "not yet accepted" (V).

## 3. Auto-balance harness design

### 3.1 Pipeline
```
GDD loops --(agent)--> economy.spec.yaml --(validate)--> headless sim --(metrics)--> objective
     ^                                                                                  |
     |        write-back (SerializedObject) -> assets -> re-sim from assets <- optimizer-+
     +---- report + parity probe in Play Mode (timeScale 1, clean save) ----------------+
```
Stages: 0 size with a throwaway model (existing Python script is enough), 1 build tables from the GDD loops, 2 optimise in-process, 3 write to assets, 4 re-simulate from the assets (round-trip check), 5 Play Mode parity probe, 6 report.

### 3.2 Simulator language: recommendation
Recommend **C# pure-logic core, run headless through Unity EditMode (or batchmode `-executeMethod`)**, with the Python script kept only as a stage-0 sizing helper.

| Criterion | C# EditMode tool | Python script |
|---|---|---|
| Formula drift | the sim calls the game's own static formulas (`EggBalanceFormula`, `Factory_*.PaintKeyboard...Price()`), so it cannot diverge | every formula is re-implemented; TBE already shows three diverging copies (2.3) |
| Reads live config | `SerializedObject` / `Factory_X.Instance` reads the real asset values (KT code defaults differ from assets, 1.1) | must parse Unity YAML (hex-encoded int arrays like `_rebirthMultiplierSteps`) or an exported JSON |
| Speed | in-process millions of ticks/s; thousands of full-game sims per second at event-step granularity | fine for small chains, slow at 1e6+ steps in pure Python |
| Availability | needs the Unity Editor open or `Unity.exe -batchmode` (the MCP link failed this session) | `py -I` works on this machine (Python 3.14.7, V), but bare `python` is the Microsoft Store stub and fails (V `python --version`). Other machines may have none |
| YAML | no parser in Unity; use a strict subset parser or JSON | stdlib has no YAML parser either; `json` is built in |
Decision rule (I): the **formula source stays in C#**; the sim core lives in `Scripts/Editor/Balance/` (or an `Economy.Sim` asmdef with no `UnityEngine` references so it can be unit tested and, if needed, compiled by `dotnet`). If Unity is unavailable the agent falls back to `py -I` stage-0 sizing and marks every result "unverified against game formulas". Spec format: author YAML for readability but have the C# reader accept the strict subset (maps, lists, scalars; no anchors) or a JSON twin; check whether Newtonsoft or YamlDotNet is already installed before adding a dependency.

### 3.3 Economy spec (YAML schema outline)
```yaml
spec_version: 1
game: break-and-steal-egg
seed: 12345            # base seed; sim uses seeds [seed .. seed+N-1]
time:
  tick_s: 1.0          # event steps are used when waits exceed tick
  horizon_days: 30
  sessions: {casual: {per_day: 2, minutes: 8}, hardcore: {per_day: 5, minutes: 25}}
currencies:
  - {id: money, type: soft, start: 0, max_log10: 300}
  - {id: gem,   type: hard, start: 0}
sources:                          # income generators
  - {id: pets, kind: rate, formula: "sum(slot_income) * cage_mult * rebirth_mult",
     bind: {class: EggBalanceFormula, method: PetIncome}}
  - {id: tap,  kind: active, per_s: "base * (1 + 0.3*level)"}
curves:                           # reusable cost/gain curves
  - {id: pickaxe_price, type: table|geometric|polynomial|piecewise, base: 200, growth: 2.05,
     bind: {asset: Factory_PaintKeyboard, fields: [_rollSizeUpgradeBasePrice, _rollSizeUpgradePriceGrowthPerLevel]}}
upgrades:
  - {id: worker_speed, curve: worker_speed_price, effect: {stat: worker_speed, per_level: 0.15}, max_level: 40}
rebirth:
  requirement: {base: 250K, growth: 4.5}
  reward: {multiplier: "1 + step*n", step: 1, keeps: [gem], resets: [money, upgrades], caps_up: {workers: 5}}
offline: {cap_h: 6, min_s: 60, rate: 0.15, ad_mult: 2}
gacha:
  - {id: egg_green, price: {gem: 10000}, weights: [35,25,25,10,5], pity: {misses: 10, forces: top_tier}}
shops:
  - {id: boost_shop, restock_s: 200, slots: 4, weights_by_world: {...}}
daily: {days: 30, rewards: [{day: 1, money: "10"}], missed_recover: rewarded_ad}
ads:
  rewarded: [{placement: offline_x2, effect: {mult: 2}}, {placement: free_gem, effect: {gem: 100, per_day: 5}}]
  interstitial: {start_s: 60, between_s: 40}
iap: [{id: cup2, price_usd: 3.99, grants: {gem: 5000}}]     # design-time numbers only
archetypes:
  casual:     {efficiency: 0.65, survival: 0.72, ad_accept: 0.1, spends_usd: 0}
  hardcore:   {efficiency: 1.20, survival: 0.96, ad_accept: 0.3, spends_usd: 0}
  ad_watcher: {efficiency: 1.00, survival: 0.88, ad_accept: 0.9, spends_usd: 0}
  payer:      {efficiency: 1.00, survival: 0.88, ad_accept: 0.3, spends_usd: {d1: 5, d7: 20}}
policy: {buy: best_payback, tie: cheapest, lookahead: 1}   # greedy by payback time
milestones: [first_pet, first_upgrade, zone_2, zone_5, first_rebirth, cage_11]
targets:                          # bands, all parameters (section 3.5)
  time_to_first_upgrade_s: {casual: [30, 90]}
  time_to_milestone_h: {zone_2: [0.1, 0.25], cage_11: {normal: [168, 252]}}
  session_len_min: [4, 15]
  ad_per_session: [0.5, 3]
  max_wait_s: {early: 300, mid: 1800}
  inflation_ratio_max: 3.0
tunables:                         # what the optimiser may change
  - {path: curves.worker_speed_price.growth, bounds: [1.05, 3.0], scale: log, snap: nice}
  - {path: rebirth.requirement.growth,       bounds: [1.5, 8.0],  scale: log}
bindings:                         # spec path -> Unity asset field, used by write-back
  - {path: curves.worker_speed_price.growth, asset: "Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_PaintKeyboard.asset", field: _workerSpeedUpgradePriceGrowthPerLevel}
measured:                         # constants taken from Play Mode, never guessed (2.2 rule 3)
  hit_interval_s: {value: 0.378, source: "clip 0.5667 / 1.5"}
```
Rules (I): every number has exactly one home (spec or game asset); `bind` ties a spec curve to the real game function so the sim calls it; unbound curves are allowed only in stage 0 and flagged in the report.

### 3.4 Player archetypes and policy
- Reuse the TBE shape (V): `efficiency` multiplies active play, `survival` is the share of valid routes, plus session counts per day. Four presets: **casual** (efficiency 0.65, 1-2 sessions/day of 5-10 min, no ads), **hardcore** (1.2, many long sessions), **ad-watcher** (accepts rewarded with high probability, uses x2 offline and free grants), **payer** (spends at chosen days; only changes which IAP grants are applied, prices come from the spec).
- Decision policy: greedy "next buy with the best payback = cost / delta_income", with an affordability wait; a second policy `save_for_goal` for gated unlocks; the skill checklist item "does buying the cheapest next upgrade always beat saving?" becomes a metric (3.5).
- Sessions: the sim alternates play and idle blocks; offline income applies the cap and rate between sessions (1.4); daily rewards and restock timers advance on game days.

### 3.5 Metrics (per archetype, mean and p10/p90 over N seeds)
| Metric | Definition | Typical band source |
|---|---|---|
| `t_first_reward`, `t_first_upgrade` | seconds to first income / first purchase | skill: first reward < 30 s, first upgrade 30-90 s; TBE first pet 30-90 s |
| `t_milestone[k]` | time to each named milestone | skill: first zone change 5-15 min, first rebirth 30-90 min; TBE new biome 8-15 min, Cage 11 7-10.5 days |
| `wait_p95`, `wait_max` by phase | longest gap between affordable purchases | skill: under about 5 min until a designed wall |
| `session_len` | minutes until the player's next buy needs more than the session budget | target band per archetype |
| `ads_per_session` | rewarded + interstitial opportunities taken per session, interstitial spacing honours the time gates | designer bands |
| `softlock` | state with no affordable purchase, zero or negative net income, or a gate requiring a resource that cannot be earned (zone speed above reachable treadmill, required pet unobtainable) | hard constraint: must be 0 |
| `inflation` | ratio of top currency income growth to price growth over a window; also `payback_time[level]` monotonic or within band (TBE: finite payback per band) | `inflation_ratio_max` |
| `dominance` | share of runs where one upgrade is the best buy for more than X% of purchases | skill: variety of best next buy |
| `bypass` | single ad/IAP/luck multiplier skipping 2+ gates | TBE acceptance |
| `completion_days` | full completion horizon under the archetype | GDD target |
| `numeric_health` | max log10 of any currency, count of NaN/Infinity, int-overflow candidates | hard constraint |

### 3.6 Objective function and acceptance
- Banded penalty per metric `m` with band [lo, hi]: `p = max(0, (lo - m)/lo, (m - hi)/hi)^2`; weights `w` per metric come from the spec (default 1, `softlock`/`numeric_health`/`bypass` are hard).
- `J = sum(w * p)` over archetypes and metrics; hard constraints violated means infeasible (J = +inf, point rejected).
- Accept when all hard constraints pass, every metric is inside its band for its archetype, and `J < epsilon` (default 1e-3). All of `lo/hi`, weights, `epsilon`, N seeds, horizon are parameters in `targets:` / `search:`, never constants in code.

### 3.7 Search method
1. Order tunables by sensitivity (one-at-a-time perturbation of +/-10%, measure change in J).
2. **Coordinate descent**: pass over tunables; for each one with a monotone effect on a milestone time (growth rates, base prices, rebirth requirement) run **bisection in log space** to land the milestone on the band centre; otherwise 5-point line search.
3. After each full pass, re-evaluate all metrics; repeat.
4. Guards: trust region (a tunable moves at most +/-50% per iteration); monotonic constraints (price(level+1) >= price(level), zone speeds increasing, rarity multipliers increasing); snap to "nice numbers" (TBE `RoundNice`) only at write-back, with a final re-sim to confirm bands still hold.
5. If J stalls, random restarts (3) with perturbed start and the same seeds; optional last resort Nelder-Mead on the 2-3 most sensitive parameters.
6. Coupling rule from TBE: when a metric depends on two curves (cage price vs income), tune the upstream income curve first, then prices, never a single downstream price alone.

### 3.8 Stop criteria (all parameters, defaults in parentheses)
- Success: acceptance (3.6) reached.
- Iteration cap (`max_iters` 60 coordinate passes) or sim budget (`max_sims` 20000, wall clock 10 min).
- No-improvement patience (8 passes with J change below 1%).
- Infeasible/structural: the same binding constraint across restarts, e.g. "Cage 11 payback below band even at growth lower bound": stop and report the structural fix needed (add sink, add multiplier, widen band) instead of looping.
- Safety: any `numeric_health` violation or non-finite sim aborts the iteration.

### 3.9 Report format (`docs/balance/<yyyy-mm-dd>-<game>-runNN.md` + `.csv`)
1. Header: spec hash, git status line, seeds, archetypes, iteration count, stop reason.
2. Parameters table: path, before, after, bounds, snapped value, bound asset field.
3. Metrics table: archetype, metric, target band, actual (mean, p10, p90), PASS/FAIL.
4. Per-iteration trace CSV: iter, tunable, value, J, binding metric.
5. Milestone timeline (time, money, levels) for each archetype.
6. Findings: binding constraints, dominated upgrades, soft-lock list, numeric health.
7. "Verified vs unverified": parity probe result (3.11), what only a device can show (real ad fill, store, performance).
Matches the TBE convention of keeping CSV baseline vs proposed in `docs/balance/` (V `current-baseline.csv`, `proposed-v1.csv`).

### 3.10 Write-back to config ScriptableObjects
- The applier reads `bindings:`; for each tunable it opens the asset with `SerializedObject.FindProperty(field)` (Factory singletons use private `[SerializeField]` fields, V KT) and sets the value; list-valued tables (TBE generated assets) go through the project's existing generator (`Gameplay_Rebalance.Run`) rather than raw field writes; hex or compact strings (`_rebirthBaseRequirementStr: 250K`) use the project's own formatter (`UtilsNumber`/`NumberHepler`).
- Never hand-edit Unity YAML (house rule); always `Undo`-less `ApplyModifiedPropertiesWithoutUndo` + `EditorUtility.SetDirty` + `AssetDatabase.SaveAssets`.
- Dry-run mode prints a before/after diff; a backup copy of the old values goes to `docs/balance/backup-<ts>.json` (the repo is not committed by the agent).
- After writing, **re-simulate from the assets**, not from the spec; mismatch between spec-run J and asset-run J above a tolerance means a binding error and the run fails.
- Scene/prefab overrides: values duplicated in prefabs (house rule forbids) are listed by a scan and reported, not edited silently.

### 3.11 Play Mode parity probe (simulator matches the game)
Run after each accepted tuning, using `playmode-script-testing` + `debug-cheats-menu`:
1. Back up the dev save; start from a clean save (QA rule 2.2); verify `Time.timeScale == 1`.
2. **Formula parity (EditMode, exact)**: for sampled levels, compare the sim's price/income/multiplier against the game function results; tolerance 0 for double arithmetic of the same code path.
3. **Scenario parity (Play Mode, +-5% default)**: set a golden state by cheat (level L, money M, rebirth R), run T seconds of game time (60-300 s) with a scripted bot or a click-by-reflection script, read earned currency, purchase availability time and the first unlock, and compare with the sim's prediction for the same scenario.
4. **Constants feedback**: measured values (hit interval, travel time, spawn rate) overwrite `measured:` in the spec and the loop reruns.
5. Optional accelerated runs: `timeScale <= 5` for wiring checks only; verdict uses normalized time and a final 1x run; restore in `finally`.
6. Restore the save, stop Play, read the Console; an exception caused by a test shortcut is a real finding.
A divergence above tolerance blocks acceptance and is reported as simulator drift (4.1).

### 3.12 Agent protocol
1. Intake: list every loop in the GDD and map it to an archetype in section 1; unmapped loops are asked about once.
2. Fill spec tables; run stage-0 sizing with the existing Python helper if Unity is unavailable.
3. Build Data/Config/Factory scripts and assets per house style (`Data_*`, `Factory_*`, SO assets) BEFORE optimisation so bindings exist.
4. Run the loop, write assets, re-sim, parity probe, report. Output a 10-line summary and the report path.
5. Never claim PASS on bands that were not simulated; list them under "unverified".

## 4. Failure modes
1. **Simulator drift**: copies of formulas or prices in the sim diverge from assets (TBE 2.3: three pet factors, 5e16 vs 5e14 Cage 11, stale EV 97.388). Mitigation: bind to game functions, read assets, add a test that fails when a hard-coded sim table differs from the asset.
2. **Code defaults vs asset values**: KT `Factory_PaintKeyboard` code defaults differ from the singleton asset on 8 fields (1.1, 1.3); always read the asset (the loaded singleton), never the field initialisers.
3. **Save pollution**: dev saves with money or unlocks invalidate every duration claim; mock IAP/ad grants persist (`Data_*` saved on exit). Mitigation: clean-save requirement, save backup/restore, "cheated" session flag from `debug-cheats-menu`.
4. **timeScale distortion**: real-time timers (pet lifetime, boss recovery, restock 200 s, interstitial gates) do not scale; normalise or test at 1x.
5. **Float overflow and precision**: `double` max about 1.8e308; `Math.Pow(growth, level)` becomes Infinity at high levels; adding income below `money * 1.1e-16` is lost once money exceeds about 9e15 (2^53), freezing slow generators; KT stores `float` multipliers/luck and CT stores `int` buffs (`PetBuffData.buffValue`) which wrap silently at 2.1e9. Idle numbers beyond 1e300 need a BigNumber type or log-domain arithmetic (store `log10`, mantissa + exponent). The sim tracks `max_log10` per currency, fails the iteration on non-finite values, and works in log space when any currency passes 1e150. Display suffix tables end at `Dc` (SAE `MoneyFormat`, 1e33): clamp, or extend the table.
6. **Policy bias**: greedy buying under-estimates smart players and over-estimates passive ones; keep the archetype set and compare policies; do not publish "completion days" from one policy.
7. **Unmodelled gates**: TBE notes list slot occupancy, route uptime and spend-vs-farm as missing; every unmodelled dependency must appear in the report as an assumption with a sensitivity (+/-20% sweep).
8. **Editor-only behaviour**: rewarded ads always succeed in the Editor (V doc 05 5.1), so ad-watcher measurements from Play Mode over-report; time-of-day (UTC day keys, offline timestamps) must be injectable (debug clock) for daily/offline tests.
9. **Overfitting to the bands**: optimiser may produce ugly numbers or a flat wall; snap to nice numbers, keep readable rarity jumps (TBE x2.5/rank), and run a final human-review table (price ladder preview like RAP `SO_RanchHatch.Preview`).
10. **Coupled retuning**: changing one table (cage price) can break another band; the loop evaluates every metric after each move, not only the one being tuned.
11. **Seed noise**: stochastic gacha/luck metrics need fixed seed sets and N large enough (TBE used 100,000 rolls for the tail); report the standard error.

## Proposed classification

| Candidate | Class | Proposed name | Must-haves |
|---|---|---|---|
| Closed-loop balance procedure | SKILL | `economy-auto-balance` | intake from GDD loops to the archetype catalogue; spec -> bind -> simulate -> measure -> adjust -> write-back -> re-sim -> parity probe; objective, acceptance and stop criteria as parameters; report; extends `economy-progression-design` |
| Headless simulator + optimiser + applier | TOOL | `balance-sim-harness` | C# pure-logic core in `Scripts/Editor/Balance/`; calls the game's formulas; reads singleton assets; archetype runner; coordinate descent + log-bisection; `SerializedObject` write-back with dry-run and backup; CSV/markdown report; `py -I` stage-0 fallback |
| Economy spec schema and presets | DATA | `economy-spec-schema` | YAML fields from 3.3; archetype presets; target-band presets (first reward, first upgrade, first rebirth, wait ceilings); bindings map; measured-constants section |
| One formula source, no duplicate tables | RULE | `rule-economy-single-source` | all prices/curves in one static class or Factory reading SO values; sim and runtime call the same functions; a test fails if a sim copy differs from an asset; code defaults never act as truth |
| Play Mode parity and QA validity | RECIPE | `recipe-economy-parity-probe` | clean-save backup/restore; timeScale 1 verdicts and restore in `finally`; golden-scenario cheat setup; +-5% tolerance; measured constants fed back; debug clock for daily/offline |
| Big-number safety | RULE | `rule-bignumber-safety` | no `int`/`float` for currency, multipliers or buffs; guard `Pow` overflow and non-finite values; precision ceiling 2^53 for additive income; log-domain or BigNumber above 1e150; display suffix clamp |
| Loop archetype library (section 1) | DATA | `economy-loop-reference` | formulas and numbers from 1.1-1.6 with file paths; used by intake to propose starting curves |

Top must-haves (6): (1) `balance-sim-harness` C# core bound to the game's formulas; (2) `economy-spec-schema` with bindings and tunables; (3) `economy-auto-balance` skill with parameterised objective and stop criteria; (4) `rule-economy-single-source` with a drift test; (5) `recipe-economy-parity-probe` (clean save, timeScale 1); (6) `rule-bignumber-safety`.
