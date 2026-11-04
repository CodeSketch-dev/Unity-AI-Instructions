# Asset kit recipes 1-8
Illustrative; verify API names in the installed SketchEngine package.

### Kit recipes (SketchEngine-first wording; KT/CodeSketch v1 names are provenance only)

Recipe 1. Config singleton with auto-collected entries. Genres: platformer, tycoon, match-3.
Bring: `ScriptableObjectSingleton<T>` base (SketchEngine equivalent, check the installed loader path), one factory class per feature, entry SO class, folder `Configs/<Feature>/`. Wire: create `Resources/<root>/ScriptableObjectSingletons/Game.Factory_<X>.asset` (name = type name), fill the array with `[AssetList(Path=..., AutoPopulate=true)]`.
```csharp
public class Factory_Pool : ScriptableObjectSingleton<Factory_Pool> {
    [AssetList(Path = "_Game/Configs/Pool/", AutoPopulate = true)]
    [SerializeField] PoolPrefabConfig[] _configs;
    [SerializeField] PoolPrefabConfig _fxHit;
    public static PoolPrefabConfig[] Configs => Instance._configs;
    public static PoolPrefabConfig FxHit => Instance._fxHit;
}
// use: var fx = PoolPrefabGlobal.Get(Factory_Pool.FxHit); ... PoolPrefabGlobal.Release(Factory_Pool.FxHit, fx);
```
Why it is built this way: assets, not code, so the owner tunes in the Inspector; static accessors keep call sites short; never create managers at runtime. Do not change: the file name must equal the type name or `Resources.Load` returns null and a second empty asset is created in the Editor.

Recipe 2. Audio library in 10 minutes. Genres: shooter, puzzle, idle.
Bring: `AudioConfig` SO, `AudioBus` enum + mixer groups (Master 10, Music 20, UI 30, Sound 40, Voice 50, Ambience 60), the generator window. Steps: drop clips into `Audios/Sfx/<Cat>/`, run the generator with prefix `Sfx_`, set `_volume`; BGM `_type=Music`, bus Music, volume 0.4. Reference configs from `Factory_Audio` fields, never raw clips.
```csharp
[SerializeField] AudioConfig _sfxWin;
public static void PlayWin() { if (Instance._sfxWin != null) AudioManager.Play(Instance._sfxWin); }
```
Do not change: SFX that play in the world are 3D with ears 0.1-4; UI sounds 2D on the UI bus so ducking works.

Recipe 3. Currency flying to the HUD. Genres: idle/tycoon, runner, puzzle meta.
Bring: `Currency_Spread_Config` (+ 3 assets), the spread script, coin prefab, end vfx/sfx. Wire: `_prefab`, `_vfxEnd`, `_sfxEnd`; keep the KT timings as a starting feel (sequence 0.5, back 0.09 x 0.5, scale 0.5, fly 0.3 after 0.5, control (0,8,0)/(6,-6,0)). Call the spread API with start world point, target HUD icon and the config; add to the balance on `reachEndDelay`.
Why: coins feel earned because the number only rises when the first coin lands; compute `reachEndDelay = sequenceDelay + scaleDuration + backDuration + flyDelay + flyDuration` instead of hard-coding.

Recipe 4. Mobile tier with one URP asset. Genres: 3D platformer, racer, 2D top-down.
Bring: `Mobile_RPAsset` (HDR can be turned off for a stricter baseline), `Mobile_Renderer`, `Device` tier detection, `AutoTiling_BumpToggle`-style global keyword. Steps: single Quality level bound to the mobile asset; per-tier switches via flags (shadows, bloom, bump, texture limit) and global keywords (`Shader.EnableKeyword`), not via many URP assets.
```csharp
void Apply(){ if (Device.IsLowEnd) Shader.EnableKeyword("_AUTOTILING_NO_BUMP"); else Shader.DisableKeyword("_AUTOTILING_NO_BUMP"); }
```
Do not copy: `ApplyQualityLevel` indices 0/2/3 unless you really define those quality levels.

Recipe 5. TMP outline presets and per-locale fonts. Genres: any.
Bring: ChangaOne SDF (dynamic) + outline presets (width 0.2 / dilate 0 / black / underlay y -0.6 alpha 0.82) and `Factory_Localize_Font`. Steps: pick the preset by size; for world text use the `Distance Field Billboard` material; add the locale font dictionary entry before shipping a language.
Why: dynamic atlas keeps the build small; locale dictionary avoids tofu boxes. Do not change `_GradientScale` per label.

Recipe 6. Weighted reward asset (daily, jackpot, gacha). Genres: idle, collectible RPG, roguelite.
Bring: SO with `[] {item, weight}` + a picker. Weights are relative (KT green box 35/25/25/10/5, price 10000); display rate can differ from true rate (`_displayRate` / `_displayOverride`), and an early-game rate can be forced (`_useRateBeforeUnlockLevel`).
```csharp
float total = 0; foreach (var r in box.Rewards) total += r.Weight;
float x = Random.value * total;
foreach (var r in box.Rewards) { if ((x -= r.Weight) <= 0) return r.Item; }
```

Recipe 7. Locked-item silhouette. Genres: collection, card, character-select.
Bring: `FlatGraySilhouette` + material; assign to the Image material when the item is locked; unlocked uses default UI material (property `_GrayColor` 0.49,0.49,0.46).

Recipe 8. 9-slice UI starter. Genres: any UI game.
Bring: `refs/p5_assets_kit` sprites (popup board, tabs on/off, price button, plate, progress bar + fill, rarity frames, glow). Set Image Type Sliced and keep PPU 100; drive progress with `fillAmount`.

### Pitfalls found
1. ScriptableObject GUIDs: moving a config type without its `.meta` breaks every asset (m_Script guid). 2. 99 "Lego" materials differ only by colour: wasted import/memory; use MaterialPropertyBlock. 3. Duplicate sprite names across `vN` folders. 4. `Device.ApplyQualityLevel` index mismatch (one Quality level). 5. Early localisation init (documented in `Factory_Localize`). 6. TEXTURE2D_ARRAY on old GLES2 devices shows magenta.

### Unverified / not read in full
Boss controller states (`Cryo Panther`, `Verity`), ShaderGraph internals, PPGlobalVolume, `Mobile_Renderer_Outline` feature settings, the exact reference count of each Packages Fx effect beyond the guid scan, Cinemachine component configuration inside prefabs.

