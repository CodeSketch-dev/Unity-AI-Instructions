# Import settings: audit table (targets for low-end Android; link to presets)

| Asset | Check (from .meta) | Target | Fix |
|---|---|---|---|
| UI/icon textures | `maxTextureSize` | <= 1024 (icons 256-512) | folder preset |
| FX/particle textures | `maxTextureSize`, mipmaps | <= 1024, mipmaps on for 3D use, off for UI sprites | preset per folder |
| 3D albedo textures | Android override present, format ASTC | override block with ASTC 6x6 (or project standard), mips on | preset + AssetPostprocessor |
| Sprites | `enableMipMap` | off | preset |
| Short SFX (< 200 KB) | `loadType` | CompressedInMemory, mono when positional or not music | preset per `Audios/Sfx` |
| Music | `loadType` | Streaming, Vorbis | preset per `Audios/BGM` |
| Long ambience | `loadType` | CompressedInMemory or Streaming | preset |
| Models | `meshCompression` | Medium/High where shape allows | model preset |
| Models | `isReadable` | off unless runtime reads the mesh (combiners need it only in Editor) | model preset |
| Models without clips | `importAnimation` | off | model preset |
| Generated meshes | stored as binary asset or FBX | no text YAML above ~5 MB | change the generator |
| TMP font atlases | atlas size | one default font, atlas <= 8 MB, no duplicate names | font asset audit |

Use `scripts/import_audit.py` for the counts per top folder. Rules and presets live in `import-presets` and `audio-import-and-mixer-optimization`; this skill only finds the offenders. RAM claims need a Memory Profiler capture; the `.meta` facts are not RAM.
