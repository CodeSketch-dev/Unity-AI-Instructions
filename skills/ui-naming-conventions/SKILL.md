---
name: ui-naming-conventions
description: Naming and folder conventions for UI prefabs and objects (Btn_, Text_, Root, Board, State_*). Use when creating UI hierarchies so builders, validators and scripts can find objects by name.
---

# UI naming conventions

Builders and validators key objects by name path (idempotent tools, `ui-popup-from-demo`), so names are an interface. From report 07 counts over KT/ME popups (VERIFIED):

- Popup root = feature name + `_Popup` (`Daily_Login_Popup`) with the Popup component; child `Root`, optional `Scale`, `Board`.
- Prefixes: `Btn_` (buttons; legacy `Button*` exists, do not add new), `Text_` or `Text`, `Icon`, `Frame` (state/selected outline), `Content`, `Layout` (HLG of bottom buttons), `Fill`, `State_*` (exclusive panels), `Notify`, `Cooldown` (radial fill), `Tab_<Type>`, `Item`.
- Row/card prefabs are separate files `<Feature>_Item.prefab` beside the popup; scripts `<Feature>_<Role>`.
- Per-state children: `BtnClaim / Missed / Today / Claimed` style, toggled by SetActive.
- Page: `Title` bar + `Btn_Back` + `Background` + `SafeArea`; popup: `Board` + `Btn_Close`.
- Folders: `Prefabs/UI/<Feature>/`, sprites under `_Art/2D/GUI/`, one atlas per domain + a master atlas; sprite import: Sprite (2D and UI), PPU 100, mipmaps off, 9-slice only for frames/boards/bars (~9%), no legacy packing tag, platform overrides for big art.
- Keep the project's existing spelling when editing an established project (e.g. a misspelled legacy folder); do not rename for style.
