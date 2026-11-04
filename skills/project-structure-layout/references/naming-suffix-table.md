# Naming suffix / prefix table

Counts are from the studio reference project (723 first-party .cs, 587 in Logic) and show how consistently the grammar is used, not targets to hit.

| Role | Pattern | Example | Where | Notes (count in reference) |
|---|---|---|---|---|
| Persistent data | `Data_<Feature>` : `DataBlock<Data_<Feature>>` | `Data_Currency` | `Scripts/Data/` | 16 of 16 derive DataBlock; static accessors `Data_Currency.Gem` |
| Registry | `Factory_<Feature>` : `ScriptableObjectSingleton<>` | `Factory_Item` | `Scripts/Factory/`, one asset each | 29 singletons + 2 static helpers; Serialized variant only for dictionaries/polymorphism |
| Event | `Event_<Feature>_<Noun>_<Verb>` : `IEvent` | `Event_Character_Dead` | `Scripts/Event/<Feature>/` | 65 files = 65 classes, ~20 folders; payload by constructor, read-only |
| Authored entry | `<Feature>_Asset` ScriptableObject | `Item_Asset` | beside the feature; assets in `Configs/<Feature>/` | 21 files; only some have `[CreateAssetMenu]`: create entries by Editor script or MCP |
| Config | `<Feature>_Config` | | feature folder | 6 |
| Static session state | `<Feature>_Static` | `Minigame_Static` | feature folder | 12; values identical for all instances, reset on load |
| Enum | `<Feature>_Type` | `Minigame_Type` | feature folder | 15 |
| Manager / master | `<Feature>_Manager`, `<Feature>_Master` | `Minigame_Master` | feature folder | per-scene master prefab sets session state in Awake |
| Owner base | `<Feature>_Component` : `MonoCached` | `Character_Component` | feature folder | only for a family that needs the owner reference; others use `MonoCachedHub<T>` |
| State | `<Feature>_State_<Name>` | `Enemy_State_Chase` | `Logic/<Feature>/State/` | `StateMachine<TEnum>` |
| UI roles | `_Item`, `_Popup`, `_Tab`, `_Button`, `_UI`, `_GUI` | `Shop_Skin_Item` | feature folder | popups spawned through the popup manager |
| Zones / detectors | `_Zone`, `_Detector`, `_Trigger` | `CameraFar_Zone` | feature folder | collision through the registry |
| Interfaces | `I<Name>` | `ICharacterCollidable` | | |
| Minigame code | `<XXX>_<Part>` (3-letter prefix) | `SKB_Keyboard` | `Logic/Minigame/<Name>/` | prefix unique per minigame |

Style
- Private fields `_camelCase` (`[SerializeField] Type _field;`), serialized prefix by role in UI classes (`_btnX`, `_txtX`, `_imgX`, `_goX`).
- Constants and shared static config `UPPER_SNAKE_CASE`. Private methods omit `private`. No `#region`, no XML docs unless a public API needs them.
- Comments and identifiers in English. One tween library (PrimeTween), one async library (UniTask).
- Never mix prefix families for one concept: no `Evt_` next to `Event_`, no `_Factory` suffix, no project-initial variants (`<Game>Kt_...`) beside the plain name.

Asset names
- Prefab = `<Feature>_<Part>`; root GameObject name equals the file name.
- Config = `<Feature>_<Name>`; audio config = `Sfx_<clip>` / `Bgm_<track>`.
- Forbidden in names: `New`, `Copy`, `Final`, `_old`, `Backup`, `test`, `tmp`, `(1)`.
