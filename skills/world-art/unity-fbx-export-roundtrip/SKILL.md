---
name: unity-fbx-export-roundtrip
description: "Use when converting Unity mesh assets or prefab models to FBX, or when a reimport mirrors geometry, changes axes, loses vertex attributes, or breaks a hierarchy."
triggers: unity fbx, export model, reimport fbx, roundtrip mesh, axis conversion, mirrored mesh, xuat fbx, chuyen mesh, mo hinh bi lat, sai truc
---

# Unity FBX export roundtrip

Preserve the source until an exported-and-reimported copy passes geometric and visual comparison. A successful export call alone proves nothing about the imported result.

1. Inspect the installed FBX Exporter version and its actual `ModelExporter` API; use the existing package. Export a temporary authored object/prefab without changing the source asset or references.
2. Dump source hierarchy/local TRS and world-space mesh positions, normals, UVs, colors, submesh triangle indices/winding, bind poses and bone weights when present. Record units and every importer option, especially axis conversion and scale.
3. Export, import to an isolated path, then dump the same data. Preserve vertex order for a direct comparison or use an explicitly documented attribute/topology mapping; vertex counts alone cannot detect mirroring or reversed faces.
4. Treat `bakeAxisConversion` as an experiment, not a universal constant. A tested exporter/importer pair can mirror X/Z with one setting and preserve them with the other. Compare both when axes differ; keep only the setting that passes the actual roundtrip.
5. Compare dumps with `python -I scripts/compare_roundtrip.py source.json imported.json --epsilon 0.000001`. Format: top-level `nodes` and `meshes`; each mesh includes `name`, `positions`, `normals`, `uvs`, `colors`, `submeshes`, `bindposes`, `boneWeights` (empty arrays for absent attributes). Nodes include path/parent/local TRS. Normals/UVs/colors and integer indices compare exactly; positional/transform float tolerance defaults to 1e-6. Investigate any mismatch instead of hiding it by widening tolerance.
6. Import materials deliberately, verify shader/texture references, and inspect a matched-camera Play capture for depth, winding, lighting and animation. Retarget references only after numeric checks and the capture pass. A failed export remains quarantined; never retarget it because the file exists.

Report exporter/importer versions, units, axis settings tried, maximum position error, attribute/topology differences, hierarchy result, screenshot path and unverified rig/platform cases. One successful static mesh does not certify skinned meshes or every exporter version.

Run helper regression checks with `python -I scripts/compare_roundtrip.py --self-test`.
