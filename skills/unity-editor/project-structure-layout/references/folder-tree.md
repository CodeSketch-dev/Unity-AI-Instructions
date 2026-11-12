# Folder tree (depth 3, generic names)

```
Assets/
  _Game/
    Audios/
      BGM/                      <Feature>/ (tracks)
      Sfx/<Feature>/            Common/ for shared UI + gameplay clips
    Configs/
      Audio/                    one AudioConfig asset per clip (Sfx_<name>.asset)
      Pool/                     PoolPrefabConfig assets
      <Feature>/                <Feature>_Asset entries (Skin, Item, Shop, Jackpot, ...)
    Fonts/                      TMP font assets, one default atlas
    Localization/               Locales/, Tables/, source csv
    Materials/<Family>/         one shared world material + per-family fallbacks
    Prefabs/
      <Feature>/                managers, systems, world pieces, popups, item prefabs
        Shop/{All,Skin,Boost,...}
      Player/                   Player root + nested Camera/GUI prefabs
      UI/                       only generic Button/, Gameplay/, Settings/ pieces
      Minigame/<Name>/          map chunks, master prefab, HUD view
    Resources/
      <framework folder>/ScriptableObjectSingletons/   Game.Factory_<X>.asset (1:1 with Factory classes)
    Scenes/                     Splash/Home first, then Minigame_<Name>[_W<n>]
    Scripts/
      Core/                     base classes, mesh combiner, device policy
      Data/                     Data_<X>.cs
      Editor/<Feature>/         editor-only tools
      Event/<Feature>/          Event_<Feature>_<Noun>_<Verb>.cs
      Factory/                  Factory_<X>.cs
      Logic/<Feature>/          runtime; Logic/Minigame/<Name>/<XXX>_<Part>.cs
      Utilities/
    Tests/{EditMode,PlayMode}
  _Art/{2D,3D,Fx,Shader,Skyboxes}
  Packages Fx/<Vendor>/   Packages Required/<Vendor>/   Plugins/
  Settings/                 URP assets (Mobile, PC), global settings, volume profile
```

Rules of thumb
- A path tells the owner what a thing is: `Prefabs/Shop/Skin/Shop_Skin_Item.prefab`, `Configs/Item/Item_Sword.asset`, `Logic/Item/Item_Equip.cs`.
- Baked or generated output (combined meshes, atlases) lives in a clearly named generated folder with a header comment in generated code and an idempotent Editor tool that regenerates it; it is never edited by hand.
- Home hub, shop, settings and HUD are features with their own folders like any minigame.
- Do not nest a second `Assets`-like tree (`_Game/_Art`, `_Game/Imported`): source art is `_Art`, vendor is outside.
