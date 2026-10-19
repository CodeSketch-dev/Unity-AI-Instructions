---
name: character-skin-importer
description: "Validate and import a new skin: catalog and prefab checker (skeleton hash, bones, materials, animator, ragdoll, camera/light, budgets) plus an Editor importer template that wires refs and bakes thumbnails. Use when adding any skin or rig, or in local batch runner over the character prefabs."
---

# Character skin importer

Design from report 19 sec 3.4 and `SkinnedMesh_Bone_Binder` (monkey-escape). Two layers: a stdlib checker that works on text YAML without Unity, and an Editor tool (template) that needs the Unity Editor.

## Static checker (tested)
`py -I <skills>/character-skin-importer/scripts/skin_validator.py catalog character-catalog.json` checks the DATA file (`assets/character-catalog.example.json`: rigs, skin types, skins, allowed types per mode, budgets, bot names): duplicate ids, unknown rig/type, unlock rules (Free price 0, Gem/Coin price from config or auto-balance, IAP needs id), slots pointing at rig bones, rig bone limit, duplicate order.
`... prefab skin.prefab --catalog character-catalog.json --rig humanoid --role bot|player [--stats stats.json]` checks a skin prefab: ordered SkinnedMeshRenderer bones equal the rig's (reports missing/extra and prints the skeleton hash on success = `UseSharedMesh` allowed), bone and material budgets, exactly one Animator, bot culling mode and shadows, updateWhenOffscreen, baked Rigidbody/joints, Camera/Light, missing scripts. Triangle and texture sizes are not in the prefab YAML: the Editor tool writes `stats.json` (`{"tris": n, "texture": px}`) for the checker. Exit 1 on any FAIL.
Reality check (read-only): on knife-tower `Character_Skin_1.prefab` it reports the baked 12 Rigidbody + 11 joints exactly as the mining report says. Skins that are nested FBX prefab instances keep their bones in the FBX, so the static bone check needs the Editor tool for those.

## Editor tool (template `assets/CharacterSkinImporter.cs.txt`, UNCOMPILED)
Deterministic, idempotent, batch-capable (`-executeMethod`) and MCP-callable. Steps: hierarchy checks, skeleton diff and bone-name rebind (reuse `SkinnedMesh_Bone_Binder` logic) or fail with the diff, mesh/material/texture budgets, animator and bounds, write serialized refs into `Character_Skin` (Animator, main SMR, slots), set layer and shadow modes, create `Character_Skin_Asset` and register it in `Factory_Character`, bake the 256x256 transparent thumbnail from the preview stage (`shop-skin-preview`), write a JSON report. Failures block registration. Use Unity MCP to run it; never hand-write YAML or .meta (`rule-editor-tool-safety`).

## Pipeline hooks
local batch runner/pre-commit: run the importer in report-only mode over `Assets/_Game/Prefabs/Character` and the catalog check; block creating a skin asset whose prefab accesses `SkinnedMeshRenderer.material` or has Rigidbody children; static check that every skin asset is in `Factory_Character`, in the shop list, has a thumbnail and a unique id. Rules: `character-rig-and-animation-contract`, `character-perf-budgets`; chain: `character-skin-system`.
