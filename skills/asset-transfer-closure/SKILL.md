---
name: asset-transfer-closure
description: Copy prefabs/models/VFX/UI/audio between Unity projects with full dependency closure and original GUIDs via a resolver script. Use for any cross-project asset move, or when Missing/pink materials appear after a copy.
---

# Asset transfer with full dependency closure

Copying a prefab alone silently drops what it points at. The goal is zero broken references after transfer, with GUIDs preserved so everything transferred earlier or later still links.

## Procedure
1. **Resolve the closure with the script, not by eye.** `scripts/resolve_closure.py` walks `guid:` references (assets and the `.meta` of models/textures, which carry material remaps) until nothing new appears, and tells you what is already in the target.
   ```
   python -I scripts/resolve_closure.py --source <ref project> --target <my project> \
       --asset Assets/Path/Thing.prefab [--asset ...] --index-cache <file outside Unity projects>
   ```
   It is read-only (dry run) by default. The first run indexes the source (about a minute for a big project); the cache makes the next runs near instant. Use `--refresh-index` if the source changed.
2. **Read the report.** Members are `present` (same GUID already in the target: skip), `missing` (to copy), plus *unresolved GUIDs* (built-in resources, registry-package assets, or genuinely absent), shader `#include` warnings, and scripts not in the target.
   - **Scripts** need a framework-aware decision: if the target has an equivalent type with the same GUID, fine; otherwise port behaviour into the target framework or isolate. Don't blind-copy code that depends on another framework (e.g. an older audio/UI stack) because that creates a parallel system.
   - **Unresolved GUIDs**: find out what they are (open the referencing asset in the source Editor) before ignoring them; a shader or texture hiding there is the usual cause of pink materials.
   - **Different GUID, same name** in the target: stop and decide remap vs keep; never silently substitute.
3. **Choose destinations** deliberately: first-party content under the project's art/game folders by feature, vendor content isolated in its own folder. Pass `--dest-prefix`; the source relative path is kept below it so related assets stay together.
4. **Apply**: rerun with `--apply` (adds `.meta` copies, GUIDs preserved; add `--allow-scripts` only after the review above). Never hand-author `.meta` or Unity YAML.
5. **Refresh the AssetDatabase** through the editor tooling and read the Console for import errors; fix importer settings that are project-specific (audio streaming/load type, texture compression, sprite borders).
6. **Verify**: open each transferred prefab; scan for Missing/null; for particle/VFX materials check both the shader and every texture property (`_MainTex`/particle texture, normal, emission); instantiate in a scene and play; confirm render-pipeline compatibility. Re-run the script in dry-run: every member should now be `present`.
7. **Record provenance** for each transferred group in `docs/asset-provenance.md` (`clone-ip-safety`).
8. **Report** the closure list, what was skipped/isolated and why, and the verification result.

## Selecting what to transfer
Transfer only content that matches the current game (e.g. don't bring creature-specific sounds or props for roles that don't exist). A larger transfer is more to verify and more to replace before release.

## Rules
- Preserving GUIDs is the point: other transferred assets reference by GUID, so regenerating metas breaks them.
- A material that exists without its texture is an incomplete transfer.
- Never edit third-party code to make an import compile; add a project-side adapter.
- Transfers can be scripted for repeatability: keep the exact command (or a mapping file for selection, e.g. rarity -> trail prefab) in the repo's docs so the transfer is reproducible and idempotent.
- The reference project stays read-only.
