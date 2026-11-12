---
name: scene-bloat-play-crash
description: "Unity crashes entering Play or scene file is huge: ExecuteAlways material components write thousands of null m_Materials overrides into nested prefab instances. Use when a scene grows to many MB, Play entry crashes in SaveScene, or after bulk authoring with material-swapping components."
triggers: crash play mode, scene too big, m_Materials override, TextureTypeComponent, SaveScene crash, BackupScenesFromSceneManager, scene bloat, unity crash
---

# Scene bloat / Play-entry crash
- Symptom: crash on Play with stack `EditorSceneManager::BackupScenesFromSceneManager -> SaveScene -> SerializableManagedRefTransfer`; scene file 10+ MB; `Temp/Unity/Editor/Crashes/*/Editor.log` shows it.
- Cause seen: an ExecuteAlways component that swaps renderer materials in edit mode left ~50k `propertyPath: m_Materials.Array.data[N]` null overrides on prefab instances in the scene.
- Check: count lines/size of the scene, then `grep -c "m_Materials.Array"`. Big-block finder: split the YAML by `--- !u!` and print the largest PrefabInstances.
- Fix: back up the scene, strip the null override entries with a regex (entry = 4 lines: target, propertyPath, value, objectReference: {fileID: 0}), reopen the scene from disk, confirm it is not dirty, enter Play.
- Prevent: authoring components must use a shared material asset plus MaterialPropertyBlock (never serialized), never per-instance material clones; check scene size after bulk authoring.
- Also reset compensation constants (colour gain) when the shader that needed them is replaced.
