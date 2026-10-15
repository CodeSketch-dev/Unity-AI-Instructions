using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace RobloxShaderKit.Editor
{
    // One owned, repeatable bake unit. MapSpec routing selects the source renderers and chunk id;
    // this class only materializes one static chunk and never touches gameplay objects.
    public static class RobloxMapBuilder
    {
        const string GeneratedRootName = "__RobloxShaderKitGenerated";
        const string GeneratedFolder = RobloxMaterialFactory.Root + "/Generated";
        const int MaxSources = 512;

        [MenuItem("Tools/Roblox Shader Kit/Bake Selected Static Chunk")]
        public static void BakeSelectedStaticChunkMenu()
        {
            BakeSelectedStaticChunk("selected");
        }

        public static GameObject BakeSelectedStaticChunk(string chunkId)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Stop Play Mode first");
            if (string.IsNullOrWhiteSpace(chunkId))
                throw new ArgumentException("Chunk id is required", nameof(chunkId));

            var sources = Selection.gameObjects
                .SelectMany(go => go.GetComponentsInChildren<MeshRenderer>(true))
                .Where(renderer => renderer.enabled && renderer.gameObject.activeInHierarchy && renderer.gameObject.isStatic)
                .Where(renderer => renderer.GetComponent<MeshFilter>()?.sharedMesh != null)
                .Distinct()
                .Take(MaxSources + 1)
                .ToArray();
            if (sources.Length == 0)
                throw new InvalidOperationException("Select at least one active static MeshRenderer with a MeshFilter");
            if (sources.Length > MaxSources)
                throw new InvalidOperationException($"Chunk source cap exceeded ({MaxSources})");

            EnsureGeneratedFolder();
            var material = RobloxMaterialFactory.Ensure();
            var root = FindOrCreateGeneratedRoot();
            var chunkName = "Chunk_" + Sanitize(chunkId);
            var existing = root.transform.Find(chunkName);
            if (existing != null)
                UnityEngine.Object.DestroyImmediate(existing.gameObject);

            var chunk = new GameObject(chunkName);
            chunk.transform.SetParent(root.transform, false);
            var filter = chunk.AddComponent<MeshFilter>();
            var renderer = chunk.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = ShadowCastingMode.On;
            renderer.receiveShadows = true;

            var combines = sources.Select(source => new CombineInstance
            {
                mesh = source.GetComponent<MeshFilter>().sharedMesh,
                transform = root.transform.worldToLocalMatrix * source.transform.localToWorldMatrix,
                subMeshIndex = 0
            }).ToArray();
            var baked = new Mesh { name = chunkName + "_Mesh", indexFormat = IndexFormat.UInt32 };
            baked.CombineMeshes(combines, true, true, false);
            RobloxSurfaceMesh.Validate(baked);

            var meshPath = GeneratedFolder + "/" + chunkName + ".mesh";
            if (AssetDatabase.LoadAssetAtPath<Mesh>(meshPath) != null)
                AssetDatabase.DeleteAsset(meshPath);
            AssetDatabase.CreateAsset(baked, meshPath);
            filter.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);

            var reportPath = GeneratedFolder + "/" + chunkName + ".report.txt";
            File.WriteAllText(ToProjectPath(reportPath),
                $"chunk={chunkId}\nsource_renderers={sources.Length}\nvertices={baked.vertexCount}\nmaterial=shared\n");
            EditorUtility.SetDirty(chunk);
            EditorSceneManager.MarkSceneDirty(chunk.scene);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            return chunk;
        }

        static GameObject FindOrCreateGeneratedRoot()
        {
            var root = GameObject.Find(GeneratedRootName);
            if (root != null) return root;
            root = new GameObject(GeneratedRootName);
            Undo.RegisterCreatedObjectUndo(root, "Create Roblox shader kit generated root");
            return root;
        }

        static void EnsureGeneratedFolder()
        {
            if (AssetDatabase.IsValidFolder(GeneratedFolder)) return;
            AssetDatabase.CreateFolder(RobloxMaterialFactory.Root, "Generated");
        }

        static string ToProjectPath(string assetPath)
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName;
            if (string.IsNullOrEmpty(projectRoot)) throw new InvalidOperationException("Unity project root unavailable");
            return Path.Combine(projectRoot, assetPath.Replace('/', Path.DirectorySeparatorChar));
        }

        static string Sanitize(string value)
        {
            foreach (var invalid in Path.GetInvalidFileNameChars()) value = value.Replace(invalid, '_');
            return value.Replace(' ', '_');
        }
    }
}
