# Combiner details

## Runtime loop (trimmed, SketchEngine-first; check the installed loader API)
```csharp
void Awake() {
    if (Loading.IsBusy) { Loading.RegisterLoadTask(p => CombineAsync(p, _budgetMsViaLoader)); _registered = true; }
}
async UniTask CombineAsync(IProgress<float> progress, float budgetMs) {
    var sw = Stopwatch.StartNew(); long budget = (long)(budgetMs * Stopwatch.Frequency / 1000f);
    for (int i = 0; i < _bakedGroups.Count; i++) {
        CombineOneGroup(_bakedGroups[i]);              // Mesh.CombineMeshes per material
        progress?.Report((i + 1f) / _bakedGroups.Count);
        if (sw.ElapsedTicks >= budget) { await UniTask.Yield(PlayerLoopTiming.LastUpdate); sw.Restart(); }
    }
    DisableLodGroups(_combinedLods);
}
```
Serialized data: `[Serializable] struct BakedRendererGroup { Material Material; MeshRenderer[] Renderers; }`.

## Reproduce checklist
1. Component with serialized baked groups; the Editor button runs your scan; runtime only combines.
2. Register as a loading task with two budgets (direct play vs loader).
3. Skip tag + dynamic keyword list; Read/Write only on combined sources.
4. Put on a SceneCombiner prefab; one-key bake in `scene-optimizer-bake`.

## Alternative: one mesh per scene
A per-object authoring component (Color32, optional base texture, tiling) plus a scene scanner that writes ONE mesh directly into pre-sized arrays (positions, normals, UV sets, vertex colour with sRGB to linear when needed) and a runtime Texture2DArray (slice 0 = white) applied through a MaterialPropertyBlock, with a vertex-colour triplanar shader. No per-object Instantiate/CombineMeshes. Exclude LODGroup, Rigidbody, CharacterController, Animator, PlayableDirector and objects with an exclude marker.

## Offline merged scene variants
Per-stage merged FBX (isReadable off, weld on, no animation) exported from an exporter scene: zero runtime cost, but tens of MB of FBX and duplicate scenes to maintain. Use only when the runtime combine cost is proven too high.
