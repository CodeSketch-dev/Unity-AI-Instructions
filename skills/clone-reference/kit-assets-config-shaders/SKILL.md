---
name: kit-assets-config-shaders
description: "Use when setting up non-prefab building blocks: config ScriptableObject + Factory singleton, audio/pool configs, mobile URP tier with shader keyword, TMP outline presets and locale fonts, sprite atlases/9-slice, localization, locked-item silhouette, weighted reward asset."
triggers: config asset, factory singleton, audio config, pool config, urp tier, shader keyword, tmp outline preset, locale font, sprite atlas, 9 slice, localization setup, silhouette shader, weighted reward, asset kit, cau hinh scriptable object, font outline, atlas, knife tower style assets
---

# Kit: assets, configs, shaders

Opt-in kit (see `prefab-kit-catalog`). Existing skills first: `config-and-factory-authoring`, `factory-singleton-template`, `audio-import-and-mixer-optimization`, `pool-everything`, `device-tier-policy`, `mobile-urp-lighting-baseline`, `one-material-world-shader`, `tmp-font-optimization`, `sprite-atlas-v2`, `ui-9slice-buttons`, `localization-pipeline`, `loot-rarity-tables`.

## 1. Ranked starter list (genre-neutral first)
| # | Item | Value | Notes |
|---|---|---|---|
| 1 | Config SO entries + a Factory `ScriptableObjectSingleton` per feature | 5 | asset file name = type name; entries auto-collected from a folder |
| 2 | Audio config assets + audio factory + generator window + mixer buses | 5 | `Sfx_<Cat>_<Name>`; reference configs, never raw clips |
| 3 | Pool prefab configs + pool factory + global pool | 5 | spawned VFX/floating text/pickups |
| 4 | One mobile URP asset + device tier flags + global shader keyword | 5 | per-tier switches, not many URP assets |
| 5 | TMP font + outline material presets + locale font factory | 5 | one preset per size |
| 6 | Sprite atlas per screen + GUI sprite sets with 9-slice borders | 5 | images/ has starter sprites |
| 7 | Currency spread config | 5 | `kit-ui-services` |
| 8 | Localization (table per locale, wrapper) | 4 | from day one |
| 9 | Locked-item silhouette shader | 4 | collection/shop/gacha |
| 10 | Daily/gacha/jackpot weighted assets, selection asset, price + IAP id pattern | 3-4 | optional live-ops |
| 11 | Triplanar auto-tiling world shader, vertex-colour + Texture2DArray combiner | 4 | optional genre pack: static 3D worlds |
| - | Game-specific shaders (typing/paint floors), weapon configs, wings | 1-2 | do not copy |

## 2. Config + Factory (rules)
- One Factory per feature: `ScriptableObjectSingleton<Factory_X>`; the asset lives under the framework's Resources singleton folder (check the installed loader path) and its FILE NAME MUST EQUAL THE TYPE NAME, otherwise `Resources.Load` returns null and a second empty asset is created.
- Static read-only accessors for call sites; build lookup dictionaries in `OnInitialize`; never create managers at runtime. Entries are small SOs under `Configs/<Feature>/`.
- Moving a config type without its `.meta` breaks every asset (`m_Script` GUID): move script + meta together (`asset-transfer-closure`, `unity-script-migration`).
- Weighted rewards: array of `{item, weight}` + picker; display rate may differ from true rate; allow a forced early-game rate; always a pity counter.

## 3. Audio and pools
Buses: Master 10, Music 20, UI 30, Sound 40, Voice 50, Ambience 60. World sfx 3D (ears 0.1-4); UI sounds 2D on the UI bus so ducking works. BGM bus Music ~0.4. Pool every repeated spawn through `PoolPrefabGlobal` + config asset.

## 4. URP tier and shader keyword
One Quality level bound to ONE mobile URP asset (512 shadow map, 1 cascade, SRP Batcher on, depth texture only if needed; HDR off for the strict baseline). Per-tier behaviour via device flags (shadows, bloom, bump, texture limit) and global keywords, e.g. `if (Device.IsLowEnd) Shader.EnableKeyword("_AUTOTILING_NO_BUMP")`. Do not hard-code quality-level indices you did not define. Texture2DArray shaders show magenta on very old GLES devices: gate by tier.

## 5. Text, sprites, localization
- TMP: dynamic font atlas (1024) keeps builds small; outline presets (face dilate 0, outline width ~0.2, black, underlay y -0.6 alpha ~0.82, gradient scale 10) applied through the material slot; world text uses the billboard SDF material (instanced). Never change gradient scale per label. Locale font dictionary (locale -> font asset) filled BEFORE shipping a language; Arabic needs an RTL package.
- Sprites: one atlas per UI theme/screen, Image Type Sliced at PPU 100, progress via `fillAmount`; never duplicate sprite names across version folders. Keep UI art tracked in git.
- Localization: keys on every label, init order documented, CSV -> table, 9 locales as reference.

## Done-check
Factory asset loads (non-null) in Play and a build; audio configs play on the right bus; pool returns objects; tier switch verified by toggling the flag; atlas/draw-call count before/after (`sprite-atlas-v2`); every label localized with outline.

## Pitfalls
~100 near-identical colour materials (use one material + vertex colour/property blocks); duplicate sprite names; unused quality-level indices; localization init after first text use.

References: [recipes](references/recipes.md), [images](references/images/README.md), [PROVENANCE](references/PROVENANCE.md).
