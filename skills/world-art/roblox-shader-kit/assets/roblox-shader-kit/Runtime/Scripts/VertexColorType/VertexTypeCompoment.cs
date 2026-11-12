using System.Collections.Generic;
using Sirenix.OdinInspector;
using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Base_VanHuy
{
    [ExecuteAlways]
    [UnityEngine.Scripting.APIUpdating.MovedFrom(true, sourceNamespace: "Base_VanHuy", sourceAssembly: "Assembly-CSharp", sourceClassName: "VertexColorEmission")]
    public partial class VertexTypeCompoment : MonoBehaviour
    {
        private static readonly int EmissionStrengthId = Shader.PropertyToID("_Emission_Strength");
        private static readonly int LegoTilingId = Shader.PropertyToID("_Lego_Tiling");
        private static readonly int CheckerTilingId = Shader.PropertyToID("_Checker_Tiling");

        [SerializeField, Delayed, Min(0f), LabelText("Emission Strength")]
        private float emissionStrength = 0f;
        [SerializeField, Delayed, Min(0.01f), LabelText("Lego Tiling")]
        private float legoTiling = 24f;
        [SerializeField, Delayed, Min(0.01f), LabelText("Checker Tiling")]
        private float checkerTiling = 8f;
        [SerializeField, ListDrawerSettings(Expanded = true, HideAddButton = true, HideRemoveButton = true, DraggableItems = false)]
        private List<VertexColorEntry> vertexColors = new List<VertexColorEntry>();
        [SerializeField, HideInInspector] private List<int> emissionVertexIndices = new List<int>();
        [SerializeField, HideInInspector] private List<int> vertexColorIndices = new List<int>();
        [SerializeField, HideInInspector] private bool hasVertexColorMap;
        [SerializeField, HideInInspector] private int dataVersion;
        [SerializeField, HideInInspector] private int vertexColorStateHash;
        [SerializeField, HideInInspector] private bool hasVertexColorStateHash;
        [SerializeField, HideInInspector] private int emissionStateHash;
        [SerializeField, HideInInspector] private bool hasEmissionStateHash;

#if UNITY_EDITOR
        private enum VertexSelectionShape { Triangle, Square, [LabelText("Mesh Island")] MeshIsland, [LabelText("UV Seam")] UVSeam }
        [SerializeField, LabelText("Selection Mode"), EnumToggleButtons]
        private VertexSelectionShape selectionMode = VertexSelectionShape.MeshIsland;
        private SelectionTopology selectionTopology;
        private (int a, int b, int c, VertexSelectionShape mode) lastSelection = (-1, -1, -1, VertexSelectionShape.Triangle);
        private readonly List<int> selectionTriangles = new List<int>();
        private readonly HashSet<int> selectionVertices = new HashSet<int>();
        private readonly HashSet<int> visitedTriangles = new HashSet<int>();
        private readonly List<Vector3> sceneVertices = new List<Vector3>();
        private readonly HashSet<(int a, int b)> previewEdges = new HashSet<(int a, int b)>();
        private Vector3[] previewVertices = System.Array.Empty<Vector3>();
        private int[] previewLineIndices = System.Array.Empty<int>();

        [SerializeField, LabelText("Paint Color")]
        private Color vertexPaintColor = Color.white;
        private static VertexTypeCompoment activeVertexSelector;
        private static bool isColorSelection;
        private static Mesh bakedSkinnedMesh;
        private static readonly Dictionary<Renderer, bool> selectionVisibility = new Dictionary<Renderer, bool>();
        private static readonly Dictionary<GameObject, bool> previousHierarchyVisibility = new Dictionary<GameObject, bool>();
        private static bool hasSelectionEditorState;
        private static Tool previousTool;
        private static bool previousToolsHidden;
        private static PivotMode previousPivotMode;
        private static PivotRotation previousPivotRotation;
        private static System.Type previousToolType;
        private static readonly Dictionary<SceneView, bool> previousSceneGizmos = new Dictionary<SceneView, bool>();
        private static readonly Dictionary<SceneView, SceneView.CameraMode> previousSceneCameraModes =
            new Dictionary<SceneView, SceneView.CameraMode>();
        private static readonly System.Reflection.PropertyInfo selectionOutlineProperty =
            typeof(Editor).Assembly.GetType("UnityEditor.AnnotationUtility")?.GetProperty(
                "showSelectionOutline", System.Reflection.BindingFlags.Static |
                System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
        private static bool? previousSelectionOutline;
#endif

        private MaterialPropertyBlock materialPropertyBlock;
        private MaterialPropertyBlock previousPropertyBlock;
        private Renderer propertyBlockRenderer;
        [SerializeField, HideInInspector] private Mesh sourceMesh;
        private Mesh writableMesh;
        private SharedMeshVariant sharedVariant;
        private static readonly List<SharedMeshVariant> sharedMeshVariants = new List<SharedMeshVariant>();

        private sealed class SharedMeshVariant
        {
            public Mesh source;
            public Mesh mesh;
            public Color[] colors;
            public List<Vector4> emission;
            public int users;
        }

        public IReadOnlyList<VertexColorEntry> VertexColors => vertexColors;

        public float EmissionStrength
        {
            get => emissionStrength;
            set
            {
                emissionStrength = Mathf.Max(0f, value);
                ApplyEmissionStrength();
            }
        }

        public float LegoTiling
        {
            get => legoTiling;
            set
            {
                legoTiling = Mathf.Max(0.01f, value);
                ApplyMaterialProperties();
            }
        }

        public float CheckerTiling
        {
            get => checkerTiling;
            set
            {
                checkerTiling = Mathf.Max(0.01f, value);
                ApplyMaterialProperties();
            }
        }

        private void OnEnable()
        {
#if UNITY_EDITOR
            Undo.undoRedoPerformed += RefreshAfterUndoRedo;
#endif
            EnableGpuInstancing();
            DisableShadowCasting();

            EnsureSharedMeshEmissionUv();
            ApplyPaintedVertexColors();
            MigrateVertexColorMap();
            EnsureVertexColorMap();
            ApplyVertexColorsToMesh();
            NormalizeEmissionVertexIndices();
            ApplyEmissionColorsToMesh();
            ApplyEmissionStrength();
        }

        private void OnDisable()
        {
            ReleaseMaterialOverrides();
            ReleaseGeneratedMesh();
#if UNITY_EDITOR
            Undo.undoRedoPerformed -= RefreshAfterUndoRedo;
            EditorApplication.delayCall -= ValidateVertexColors;
            if (activeVertexSelector == this)
            {
                EditorApplication.delayCall -= FinishSelectionDisable;
                EditorApplication.delayCall += FinishSelectionDisable;
                return;
            }
#endif
        }

        private void OnDestroy()
        {
#if UNITY_EDITOR
            if (activeVertexSelector == this)
                StopVertexSelection();
#endif
            ReleaseMaterialOverrides();
            ReleaseGeneratedMesh();
        }

        private void OnValidate()
        {
#if UNITY_EDITOR
            EditorApplication.delayCall -= ValidateVertexColors;
            EditorApplication.delayCall += ValidateVertexColors;
#endif
        }

#if UNITY_EDITOR
        private void ValidateVertexColors()
        {
            if (this == null || !isActiveAndEnabled)
                return;

            ApplyMaterialProperties();
            if (Application.isPlaying)
                return;

            EnsureSharedMeshEmissionUv();
            if (dataVersion != 6)
                ApplyPaintedVertexColors();
            MigrateVertexColorMap();

            EnsureVertexColorMap();
            NormalizeEmissionVertexIndices();
            if (!hasVertexColorStateHash || vertexColorStateHash != GetVertexColorStateHash())
                ApplyVertexColorsToMesh();
            if (!hasEmissionStateHash || emissionStateHash != GetEmissionStateHash())
                ApplyEmissionColorsToMesh();
            CacheStateHashes();
        }
#endif

        private void MigrateVertexColorMap()
        {
            if (dataVersion == 6)
                return;

            dataVersion = 6;
            hasVertexColorMap = false;
            vertexColorIndices.Clear();
            hasVertexColorStateHash = false;
            hasEmissionStateHash = false;
        }

        private void CacheStateHashes()
        {
            vertexColorStateHash = GetVertexColorStateHash();
            hasVertexColorStateHash = true;
            emissionStateHash = GetEmissionStateHash();
            hasEmissionStateHash = true;
        }

        [SerializeField, HideInInspector] private Color[] paintedVertexColors = System.Array.Empty<Color>();

        private void ApplyPaintedVertexColors()
        {
            Mesh mesh = GetSourceMesh();
            if (mesh == null || paintedVertexColors.Length != mesh.vertexCount ||
                !EnsureMeshReadable(mesh) || MeshColorsMatch(mesh, paintedVertexColors))
                return;

            mesh = GetWritableMesh();
            if (mesh == null)
                return;
            mesh.colors = (Color[])paintedVertexColors.Clone();
            CommitMeshChanges(mesh);
        }

        private void LoadVertexColors()
        {
            Mesh mesh = GetSourceMesh();
            if (mesh == null)
            {
                vertexColors.Clear();
                vertexColorIndices.Clear();
                hasVertexColorMap = false;
                Debug.LogWarning($"{name} needs a MeshFilter or SkinnedMeshRenderer with a mesh.", this);
                return;
            }

            if (!EnsureMeshReadable(mesh))
            {
                return;
            }

            Color[] meshColors = mesh.colors;
            var previousEntries = new List<VertexColorEntry>(vertexColors);

            vertexColors.Clear();
            vertexColorIndices.Clear();

            if (meshColors.Length != mesh.vertexCount)
            {
                meshColors = new Color[mesh.vertexCount];
                for (int i = 0; i < meshColors.Length; i++)
                    meshColors[i] = Color.white;
            }

            Dictionary<Color, int> colorToIndex = new Dictionary<Color, int>();
            foreach (Color color in meshColors)
            {
                if (!colorToIndex.TryGetValue(color, out int colorIndex))
                {
                    colorIndex = vertexColors.FindIndex(entry => SamePaletteColor(entry.color, color));
                    if (colorIndex < 0)
                    {
                        bool emission = false;
                        Color paletteColor = color;
                        bool foundPreviousColor = false;
                        foreach (VertexColorEntry entry in previousEntries)
                        {
                            if (!SamePaletteColor(entry.color, color))
                                continue;
                            if (!foundPreviousColor)
                            {
                                paletteColor = entry.color;
                                foundPreviousColor = true;
                            }
                            emission |= entry.emission;
                        }
                        colorIndex = vertexColors.Count;
                        vertexColors.Add(new VertexColorEntry { color = paletteColor, emission = emission });
                    }
                    colorToIndex.Add(color, colorIndex);
                }

                vertexColorIndices.Add(colorIndex);
            }

            hasVertexColorMap = true;
            hasEmissionStateHash = false;
        }

        private static bool SamePaletteColor(Color first, Color second)
        {
            bool ldr = first.r >= 0f && first.r <= 1f && first.g >= 0f && first.g <= 1f &&
                       first.b >= 0f && first.b <= 1f && first.a >= 0f && first.a <= 1f &&
                       second.r >= 0f && second.r <= 1f && second.g >= 0f && second.g <= 1f &&
                       second.b >= 0f && second.b <= 1f && second.a >= 0f && second.a <= 1f;
            if (ldr)
                return ((Color32)first).Equals((Color32)second);

            const float tolerance = 0.0001f;
            return Mathf.Abs(first.r - second.r) <= tolerance &&
                   Mathf.Abs(first.g - second.g) <= tolerance &&
                   Mathf.Abs(first.b - second.b) <= tolerance &&
                   Mathf.Abs(first.a - second.a) <= tolerance;
        }

        private void EnsureVertexColorMap()
        {
            Mesh mesh = GetSourceMesh();
            if (mesh == null ||
                (hasVertexColorMap && vertexColors.Count > 0 && vertexColorIndices.Count == mesh.vertexCount))
            {
                return;
            }

            LoadVertexColors();
        }

        private void ApplyVertexColorsToMesh()
        {
            Mesh mesh = GetSourceMesh();
            if (mesh == null)
            {
                Debug.LogWarning($"{name} needs a MeshFilter or SkinnedMeshRenderer with a mesh.", this);
                return;
            }

            if (!EnsureMeshReadable(mesh))
                return;

            if (!hasVertexColorMap || vertexColorIndices.Count != mesh.vertexCount)
            {
                LoadVertexColors();
                Debug.LogWarning("Vertex color mapping was initialized. Edit the color again, then apply it.", this);
                return;
            }

            Color[] meshColors = new Color[mesh.vertexCount];
            for (int vertexIndex = 0; vertexIndex < meshColors.Length; vertexIndex++)
            {
                int colorIndex = vertexColorIndices[vertexIndex];
                if (colorIndex < 0 || colorIndex >= vertexColors.Count)
                {
                    Debug.LogWarning("The color palette was resized. Load the mesh colors again before applying.", this);
                    return;
                }

                meshColors[vertexIndex] = vertexColors[colorIndex].color;
            }

            if (MeshColorsMatch(mesh, meshColors))
                return;

            mesh = GetWritableMesh();
            if (mesh == null)
                return;
            mesh.colors = meshColors;
            paintedVertexColors = (Color[])meshColors.Clone();
            CommitMeshChanges(mesh);
        }


        private void ApplyEmissionColorsToMesh()
        {
            EnsureSharedMeshEmissionUv();
            Mesh mesh = GetSourceMesh();
            if (mesh == null)
            {
                Debug.LogWarning($"{name} needs a MeshFilter or SkinnedMeshRenderer with a mesh.", this);
                return;
            }

            if (!EnsureMeshReadable(mesh))
            {
                return;
            }

            EnsureVertexColorMap();
            bool[] emissionMask = new bool[mesh.vertexCount];
            bool hasEmission = false;
            foreach (int vertexIndex in emissionVertexIndices)
            {
                if (vertexIndex >= 0 && vertexIndex < emissionMask.Length)
                {
                    emissionMask[vertexIndex] = true;
                    hasEmission = true;
                }
            }
            for (int vertexIndex = 0; vertexIndex < emissionMask.Length; vertexIndex++)
            {
                int colorIndex = hasVertexColorMap && vertexColorIndices.Count == mesh.vertexCount
                    ? vertexColorIndices[vertexIndex] : -1;
                emissionMask[vertexIndex] |= colorIndex >= 0 && colorIndex < vertexColors.Count &&
                                             vertexColors[colorIndex].emission;
                hasEmission |= emissionMask[vertexIndex];
            }

            List<Vector4> emission = BuildEmissionUv(mesh.colors, mesh.vertexCount, emissionMask);
            Mesh original = GetOriginalMesh();
            if (original != null && MeshColorsMatch(original, mesh.colors) &&
                (!hasEmission || MeshEmissionMatches(original, emission)))
            {
                ReleaseGeneratedMesh();
                return;
            }

            if (sharedVariant != null && MeshEmissionMatches(mesh, emission))
                return;

            bool emissionUnchanged = MeshEmissionMatches(mesh, emission);
            mesh = GetWritableMesh();
            if (mesh == null)
                return;
            if (!emissionUnchanged)
            {
                mesh.SetUVs(2, emission);
                CommitMeshChanges(mesh);
            }
            ShareCompletedMesh(mesh, mesh.colors, emission);
        }

        private static List<Vector4> BuildEmissionUv(Color[] colors, int vertexCount, bool[] mask)
        {
            var emission = new List<Vector4>(vertexCount);
            for (int i = 0; i < vertexCount; i++)
            {
                Color color = mask[i]
                    ? (colors.Length == vertexCount ? colors[i] : Color.white)
                    : Color.clear;
                emission.Add(new Vector4(color.r, color.g, color.b, color.a));
            }
            return emission;
        }

        private void ApplyEmissionStrength()
        {
            ApplyMaterialProperties();
        }

        private void EnableGpuInstancing()
        {
            Renderer renderer = GetMeshRenderer();
            if (renderer == null)
                return;

            foreach (Material material in renderer.sharedMaterials)
            {
                if (material != null)
                    material.enableInstancing = true;
            }
        }

        private void DisableShadowCasting()
        {
            Renderer renderer = GetMeshRenderer();
            if (renderer != null)
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        private void ApplyMaterialProperties()
        {
            if (!isActiveAndEnabled)
                return;
            Renderer renderer = GetMeshRenderer();
            if (renderer == null)
            {
                return;
            }

            if (propertyBlockRenderer != renderer)
            {
                ReleaseMaterialOverrides();
                previousPropertyBlock = new MaterialPropertyBlock();
                renderer.GetPropertyBlock(previousPropertyBlock);
                propertyBlockRenderer = renderer;
            }
            materialPropertyBlock ??= new MaterialPropertyBlock();
            renderer.GetPropertyBlock(materialPropertyBlock);
            if (materialPropertyBlock.HasFloat(EmissionStrengthId) && materialPropertyBlock.HasFloat(LegoTilingId) &&
                materialPropertyBlock.HasFloat(CheckerTilingId) &&
                materialPropertyBlock.GetFloat(EmissionStrengthId).Equals(emissionStrength) &&
                materialPropertyBlock.GetFloat(LegoTilingId).Equals(legoTiling) &&
                materialPropertyBlock.GetFloat(CheckerTilingId).Equals(checkerTiling))
            {
                ApplyMetalAppearance();
                return;
            }
            materialPropertyBlock.SetFloat(EmissionStrengthId, emissionStrength);
            materialPropertyBlock.SetFloat(LegoTilingId, legoTiling);
            materialPropertyBlock.SetFloat(CheckerTilingId, checkerTiling);
            renderer.SetPropertyBlock(materialPropertyBlock);
            ApplyMetalAppearance();
        }

        private void ReleaseMaterialOverrides()
        {
            ReleaseMetalAppearance();
            if (propertyBlockRenderer != null)
            {
                propertyBlockRenderer.SetPropertyBlock(previousPropertyBlock == null || previousPropertyBlock.isEmpty ? null : previousPropertyBlock);
                propertyBlockRenderer = null;
                previousPropertyBlock = null;
            }
        }

        [Button("Revert Vertex Colors")]
        public void RevertVertexColors()
        {
            Mesh original = GetOriginalMesh();
            if (original == null)
            {
                Debug.LogWarning($"{name} needs a MeshFilter or SkinnedMeshRenderer with a mesh.", this);
                return;
            }

            if (!EnsureMeshReadable(original))
            {
                original = GetOriginalMesh();
                if (original == null || !original.isReadable)
                    return;
            }

#if UNITY_EDITOR
            Undo.RegisterCompleteObjectUndo(this, "Revert Vertex Colors");
#endif
            paintedVertexColors = System.Array.Empty<Color>();
            ReleaseGeneratedMesh();
#if UNITY_EDITOR
            RevertMeshPrefabOverride(original);
#endif
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            MeshFilter meshFilter = skinnedMeshRenderer == null ? GetMeshFilter() : null;
            if ((skinnedMeshRenderer != null && skinnedMeshRenderer.sharedMesh != original) ||
                (meshFilter != null && meshFilter.sharedMesh != original))
                AssignRendererMesh(original);
            sourceMesh = original;
            LoadVertexColors();
            ApplyEmissionColorsToMesh();
            CacheStateHashes();

#if UNITY_EDITOR
            UnityEditor.EditorUtility.SetDirty(this);
            PrefabUtility.RecordPrefabInstancePropertyModifications(this);
            RevertMatchingVertexColorOverrides();
            SceneView.RepaintAll();
#endif
        }

        [Button("Revert Emission Colors")]
        public void RevertEmissionColors()
        {
#if UNITY_EDITOR
            Undo.RegisterCompleteObjectUndo(this, "Revert Emission Colors");
#endif
            foreach (VertexColorEntry entry in vertexColors)
                entry.emission = false;
            emissionVertexIndices.Clear();
            ApplyEmissionColorsToMesh();
            CacheStateHashes();

#if UNITY_EDITOR
            EditorUtility.SetDirty(this);
            PrefabUtility.RecordPrefabInstancePropertyModifications(this);
            SceneView.RepaintAll();
#endif
        }


        private Mesh GetSourceMesh()
        {
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            if (skinnedMeshRenderer != null)
                return skinnedMeshRenderer.sharedMesh != null ? skinnedMeshRenderer.sharedMesh : sourceMesh;

            MeshFilter meshFilter = GetMeshFilter();
            if (meshFilter != null && meshFilter.sharedMesh != null)
            {
                return meshFilter.sharedMesh;
            }

            return sourceMesh;
        }

        private Mesh GetOriginalMesh()
        {
            Mesh current = GetSourceMesh();
            bool generated = current != null &&
                             (current == writableMesh ||
                              sharedVariant != null && current == sharedVariant.mesh ||
                              current != sourceMesh &&
                              (current.hideFlags & HideFlags.DontSave) != 0);
            if (!generated && current != null)
                return current;
            if (sourceMesh != null)
                return sourceMesh;
#if UNITY_EDITOR
            Component meshComponent = GetSkinnedMeshRenderer();
            meshComponent ??= GetMeshFilter();
            Component prefabComponent = meshComponent != null
                ? PrefabUtility.GetCorrespondingObjectFromSource(meshComponent)
                : null;
            return prefabComponent is SkinnedMeshRenderer skinned
                ? skinned.sharedMesh
                : (prefabComponent as MeshFilter)?.sharedMesh;
#else
            return null;
#endif
        }

        private static bool MeshColorsMatch(Mesh mesh, Color[] colors)
        {
            Color[] current = mesh.colors;
            if (current.Length == 0)
            {
                foreach (Color color in colors)
                    if (!color.Equals(Color.white))
                        return false;
                return true;
            }

            if (current.Length != colors.Length)
                return false;
            for (int i = 0; i < colors.Length; i++)
                if (!current[i].Equals(colors[i]))
                    return false;
            return true;
        }

        private static bool MeshEmissionMatches(Mesh mesh, List<Vector4> emission)
        {
            var current = new List<Vector4>();
            mesh.GetUVs(2, current);
            if (current.Count != emission.Count)
                return false;
            for (int i = 0; i < emission.Count; i++)
                if (!current[i].Equals(emission[i]))
                    return false;
            return true;
        }

        private void EnsureSharedMeshEmissionUv()
        {
            Mesh original = GetOriginalMesh();
            if (original == null || !EnsureMeshReadable(original))
                return;

            var uv = new List<Vector4>();
            original.GetUVs(2, uv);
            if (uv.Count == original.vertexCount)
                return;

            uv.Clear();
            for (int i = 0; i < original.vertexCount; i++)
                uv.Add(Vector4.zero);
            original.SetUVs(2, uv);
            CommitMeshChanges(original);
        }

        private Renderer GetMeshRenderer()
        {
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            if (skinnedMeshRenderer != null)
                return skinnedMeshRenderer;

            return GetComponent<MeshRenderer>() ??
                   GetComponentInParent<MeshRenderer>() ??
                   GetComponentInChildren<MeshRenderer>();
        }

        private SkinnedMeshRenderer GetSkinnedMeshRenderer()
        {
            return GetComponent<SkinnedMeshRenderer>() ??
                   GetComponentInParent<SkinnedMeshRenderer>() ??
                   GetComponentInChildren<SkinnedMeshRenderer>();
        }

        private MeshFilter GetMeshFilter()
        {
            return GetComponent<MeshFilter>() ??
                   GetComponentInParent<MeshFilter>() ??
                   GetComponentInChildren<MeshFilter>();
        }

        private Transform GetMeshTransform()
        {
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            if (skinnedMeshRenderer != null)
                return skinnedMeshRenderer.transform;

            MeshFilter meshFilter = GetMeshFilter();
            return meshFilter != null ? meshFilter.transform : transform;
        }

        private Mesh GetWritableMesh()
        {
            Mesh currentMesh = GetSourceMesh();
            if (currentMesh == null || !EnsureMeshReadable(currentMesh))
                return null;

            if (currentMesh == writableMesh)
                return writableMesh;

            if (sharedVariant != null && sharedVariant.mesh == currentMesh && sharedVariant.users == 1)
            {
                sharedMeshVariants.Remove(sharedVariant);
                writableMesh = currentMesh;
                sharedVariant = null;
                return writableMesh;
            }

            Mesh original = currentMesh;
            foreach (SharedMeshVariant variant in sharedMeshVariants)
            {
                if (variant.mesh == currentMesh)
                {
                    original = variant.source;
                    break;
                }
            }

            Mesh copy = Instantiate(currentMesh);
            copy.name = original.name + " (Vertex Colors)";
            copy.hideFlags = HideFlags.HideAndDontSave;
            ReleaseGeneratedMesh(false);
            sourceMesh = original;
            writableMesh = copy;
            AssignRendererMesh(copy);
            return copy;
        }

        private void AssignRendererMesh(Mesh mesh)
        {
            SkinnedMeshRenderer skinned = GetSkinnedMeshRenderer();
            if (skinned != null)
                skinned.sharedMesh = mesh;
            else
            {
                MeshFilter filter = GetMeshFilter();
                if (filter != null)
                    filter.sharedMesh = mesh;
            }
        }

        private void ShareCompletedMesh(Mesh mesh, Color[] colors, List<Vector4> emission)
        {
            foreach (SharedMeshVariant variant in sharedMeshVariants)
            {
                if (variant.source != sourceMesh || variant.colors.Length != colors.Length ||
                    variant.emission.Count != emission.Count)
                    continue;

                bool matches = true;
                for (int i = 0; i < colors.Length && matches; i++)
                    matches = variant.colors[i].Equals(colors[i]);
                for (int i = 0; i < emission.Count && matches; i++)
                    matches = variant.emission[i].Equals(emission[i]);
                if (!matches)
                    continue;

                sharedVariant = variant;
                variant.users++;
                writableMesh = null;
                AssignRendererMesh(variant.mesh);
                DestroyGeneratedMesh(mesh);
                return;
            }

            sharedVariant = new SharedMeshVariant
            {
                source = sourceMesh, mesh = mesh, colors = colors, emission = emission, users = 1
            };
            sharedMeshVariants.Add(sharedVariant);
            writableMesh = null;
        }

        private void ReleaseGeneratedMesh(bool restoreRendererMesh = true)
        {
            Mesh generated = writableMesh != null ? writableMesh : sharedVariant?.mesh;
            if (restoreRendererMesh && generated != null && GetSourceMesh() == generated)
                RestoreRendererMesh();
            if (writableMesh != null)
                DestroyGeneratedMesh(writableMesh);
            writableMesh = null;
            if (sharedVariant == null)
                return;
            if (--sharedVariant.users == 0)
            {
                sharedMeshVariants.Remove(sharedVariant);
                DestroyGeneratedMesh(sharedVariant.mesh);
            }
            sharedVariant = null;
        }

        private void RestoreRendererMesh()
        {
#if UNITY_EDITOR
            if (RevertMeshPrefabOverride(sourceMesh))
                return;
#endif
            AssignRendererMesh(sourceMesh);
        }

#if UNITY_EDITOR
        private bool RevertMeshPrefabOverride(Mesh original)
        {
            if (Application.isPlaying)
                return false;

            Component meshComponent = GetSkinnedMeshRenderer();
            meshComponent ??= GetMeshFilter();
            if (meshComponent == null || !PrefabUtility.IsPartOfPrefabInstance(meshComponent))
                return false;

            Component prefabComponent = PrefabUtility.GetCorrespondingObjectFromSource(meshComponent);
            Mesh prefabMesh = prefabComponent is SkinnedMeshRenderer skinned
                ? skinned.sharedMesh
                : (prefabComponent as MeshFilter)?.sharedMesh;
            if (prefabMesh != original)
                return false;

            SerializedProperty meshProperty = new SerializedObject(meshComponent).FindProperty("m_Mesh");
            if (meshProperty == null || !meshProperty.prefabOverride)
                return false;

            PrefabUtility.RevertPropertyOverride(meshProperty, InteractionMode.AutomatedAction);
            return true;
        }

        private void RevertMatchingVertexColorOverrides()
        {
            if (Application.isPlaying || !PrefabUtility.IsPartOfPrefabInstance(this))
                return;

            VertexTypeCompoment prefabComponent = PrefabUtility.GetCorrespondingObjectFromSource(this);
            if (prefabComponent == null)
                return;

            SerializedObject serialized = new SerializedObject(this);
            if (prefabComponent.paintedVertexColors != null && prefabComponent.paintedVertexColors.Length == 0)
                RevertMatchingProperty(serialized, "paintedVertexColors");

            if (vertexColors.Count == prefabComponent.vertexColors.Count)
            {
                bool samePalette = true;
                for (int i = 0; i < vertexColors.Count; i++)
                {
                    if (vertexColors[i].color.Equals(prefabComponent.vertexColors[i].color) &&
                        vertexColors[i].emission == prefabComponent.vertexColors[i].emission)
                        continue;
                    samePalette = false;
                    break;
                }
                if (samePalette)
                    RevertMatchingProperty(serialized, "vertexColors");
            }

            if (vertexColorIndices.Count == prefabComponent.vertexColorIndices.Count)
            {
                bool sameIndices = true;
                for (int i = 0; i < vertexColorIndices.Count; i++)
                {
                    if (vertexColorIndices[i] == prefabComponent.vertexColorIndices[i])
                        continue;
                    sameIndices = false;
                    break;
                }
                if (sameIndices)
                    RevertMatchingProperty(serialized, "vertexColorIndices");
            }
        }

        private static void RevertMatchingProperty(SerializedObject serialized, string propertyName)
        {
            serialized.Update();
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property != null && property.prefabOverride)
                PrefabUtility.RevertPropertyOverride(property, InteractionMode.AutomatedAction);
        }
#endif

        private static void DestroyGeneratedMesh(Mesh mesh)
        {
            if (Application.isPlaying)
                Destroy(mesh);
            else
                DestroyImmediate(mesh);
        }

        private void CommitMeshChanges(Mesh mesh)
        {
            mesh.UploadMeshData(false);
#if UNITY_EDITOR
            UnityEditor.EditorUtility.SetDirty(mesh);
#endif
        }

        private bool EnsureMeshReadable(Mesh mesh)
        {
            if (mesh.isReadable)
            {
                return true;
            }

#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                string assetPath = AssetDatabase.GetAssetPath(mesh);
                if (AssetImporter.GetAtPath(assetPath) is ModelImporter modelImporter)
                {
                    modelImporter.isReadable = true;
                    modelImporter.SaveAndReimport();
                    Debug.Log($"Enabled Read/Write for model '{assetPath}'.", this);
                    return false;
                }
            }
#endif

            Debug.LogError($"Mesh '{mesh.name}' is not readable. Enable Read/Write in its model import settings, then rebuild.", this);
            return false;
        }

        private int GetEmissionStateHash()
        {
            int hash = 17;
            foreach (VertexColorEntry entry in vertexColors)
            {
                hash = hash * 31 + entry.color.GetHashCode();
                hash = hash * 31 + (entry.emission ? 1 : 0);
            }

            foreach (int vertexIndex in emissionVertexIndices)
            {
                hash = hash * 31 + vertexIndex;
            }

            foreach (int colorIndex in vertexColorIndices)
                hash = hash * 31 + colorIndex;

            return hash;
        }


        private void NormalizeEmissionVertexIndices()
        {
            Mesh mesh = GetSourceMesh();
            int vertexCount = mesh != null ? mesh.vertexCount : 0;
            HashSet<int> uniqueIndices = new HashSet<int>();
            emissionVertexIndices.RemoveAll(vertexIndex =>
                vertexIndex < 0 || vertexIndex >= vertexCount || !uniqueIndices.Add(vertexIndex));
        }

        private int GetVertexColorStateHash()
        {
            int hash = 17;
            foreach (VertexColorEntry entry in vertexColors)
            {
                hash = hash * 31 + entry.color.GetHashCode();
            }

            foreach (int colorIndex in vertexColorIndices)
                hash = hash * 31 + colorIndex;

            return hash;
        }


        [System.Serializable, InlineProperty]
        public class VertexColorEntry
        {
            [HideLabel, HorizontalGroup("Row", Width = 0.75f)] public Color color;
            [LabelText("Emission"), ToggleLeft, HorizontalGroup("Row")] public bool emission;
        }

#if UNITY_EDITOR
        [GUIColor(nameof(GetVertexSelectionModeColor))]
        [Button("Emission Vertex Selection (Green: ON / Red: OFF)")]
        private void ToggleVertexSelectionMode()
        {
            if (activeVertexSelector == this && !isColorSelection)
            {
                StopVertexSelection();
            }
            else
            {
                StartVertexSelection();
            }
        }

        [GUIColor(nameof(GetColorSelectionModeColor))]
        [Button("Color Vertex Selection (Green: ON / Red: OFF)")]
        private void ToggleColorSelectionMode()
        {
            if (activeVertexSelector == this && isColorSelection)
                StopVertexSelection();
            else
            {
                StartVertexSelection();
                isColorSelection = activeVertexSelector == this;
            }
        }

        private Color GetColorSelectionModeColor()
        {
            return activeVertexSelector == this && isColorSelection ? Color.green : Color.red;
        }

        private void RefreshAfterUndoRedo()
        {
            EditorApplication.delayCall -= ValidateVertexColors;
            ApplyPaintedVertexColors();
            EnsureVertexColorMap();
            ApplyVertexColorsToMesh();
            ApplyEmissionColorsToMesh();
            ApplyMaterialProperties();
            CacheStateHashes();
            if (activeVertexSelector == this)
            {
                ApplyHierarchyIsolation();
                LockVertexSelectionTools();
            }
            SceneView.RepaintAll();
        }

        private void PaintTriangleVertices(int vertexA, int vertexB, int vertexC)
        {
            ExpandSelection(vertexA, vertexB, vertexC);
            Mesh mesh = GetSourceMesh();
            if (mesh == null || !EnsureMeshReadable(mesh))
                return;
            if (vertexA < 0 || vertexB < 0 || vertexC < 0 ||
                vertexA >= mesh.vertexCount || vertexB >= mesh.vertexCount || vertexC >= mesh.vertexCount)
                return;

            Color[] colors = mesh.colors;
            if (colors.Length != mesh.vertexCount)
            {
                colors = new Color[mesh.vertexCount];
                for (int i = 0; i < colors.Length; i++)
                    colors[i] = Color.white;
            }

            EnsureVertexColorMap();
            Color paintColor = vertexPaintColor;
            foreach (VertexColorEntry entry in vertexColors)
            {
                if (!SamePaletteColor(entry.color, paintColor))
                    continue;
                paintColor = entry.color;
                break;
            }
            bool colorChanged = false;
            foreach (int vertex in selectionVertices)
                colorChanged |= !colors[vertex].Equals(paintColor);
            if (!colorChanged)
                return;

            mesh = GetWritableMesh();
            if (mesh == null)
                return;
            if (paintedVertexColors.Length != colors.Length)
                paintedVertexColors = (Color[])colors.Clone();
            Undo.IncrementCurrentGroup();
            Undo.RegisterCompleteObjectUndo(this, "Paint Vertex Colors");
            foreach (int vertex in selectionVertices)
                colors[vertex] = paintColor;
            mesh.colors = colors;
            paintedVertexColors = (Color[])colors.Clone();
            LoadVertexColors();
            ApplyEmissionColorsToMesh();
            CacheStateHashes();
            EditorUtility.SetDirty(this);
            PrefabUtility.RecordPrefabInstancePropertyModifications(this);
            SceneView.RepaintAll();
        }

#endif

#if UNITY_EDITOR
        private void StartVertexSelection()
        {
            StopVertexSelection();
            selectionMode = VertexSelectionShape.MeshIsland;
            selectionTopology = null;
            Mesh mesh = GetSourceMesh();
            if (mesh == null || !EnsureMeshReadable(mesh))
                return;
            activeVertexSelector = this;
            previousTool = Tools.current;
            previousToolType = UnityEditor.EditorTools.ToolManager.activeToolType;
            previousToolsHidden = Tools.hidden;
            previousPivotMode = Tools.pivotMode;
            previousPivotRotation = Tools.pivotRotation;
            previousSelectionOutline = selectionOutlineProperty?.GetValue(null) as bool?;
            hasSelectionEditorState = true;

            var stage = UnityEditor.SceneManagement.StageUtility.GetStageHandle(gameObject);
            foreach (Renderer sceneRenderer in Resources.FindObjectsOfTypeAll<Renderer>())
            {
                GameObject sceneObject = sceneRenderer.gameObject;
                if (!sceneObject.scene.IsValid() || !sceneObject.scene.isLoaded ||
                    UnityEditor.SceneManagement.StageUtility.GetStageHandle(sceneObject) != stage)
                    continue;

                selectionVisibility[sceneRenderer] = sceneRenderer.forceRenderingOff;
            }

            foreach (var entry in selectionVisibility)
                entry.Key.forceRenderingOff = !IsSelectionTargetRenderer(entry.Key);

            ApplyHierarchyIsolation();
            EditorApplication.hierarchyChanged += ApplyHierarchyIsolation;

            Selection.activeGameObject = gameObject;
            EditorApplication.update += LockVertexSelectionTools;
            UnityEditor.EditorTools.ToolManager.activeToolChanged += LockVertexSelectionTools;
            AssemblyReloadEvents.beforeAssemblyReload += StopVertexSelection;
            EditorApplication.quitting += StopVertexSelection;
            EditorApplication.playModeStateChanged += StopSelectionOnPlayModeChange;
            LockVertexSelectionTools();
            SceneView.duringSceneGui += OnSceneGUI;
            SceneView.duringSceneGui += DrawVertexSelectionPreview;
            SceneView.RepaintAll();
            EditorApplication.RepaintHierarchyWindow();
        }

        private static void StopVertexSelection()
        {
            EditorApplication.delayCall -= FinishSelectionDisable;
            EditorApplication.hierarchyChanged -= ApplyHierarchyIsolation;
            SceneView.duringSceneGui -= OnSceneGUI;
            SceneView.duringSceneGui -= DrawVertexSelectionPreview;
            EditorApplication.update -= LockVertexSelectionTools;
            UnityEditor.EditorTools.ToolManager.activeToolChanged -= LockVertexSelectionTools;
            AssemblyReloadEvents.beforeAssemblyReload -= StopVertexSelection;
            EditorApplication.quitting -= StopVertexSelection;
            EditorApplication.playModeStateChanged -= StopSelectionOnPlayModeChange;
            activeVertexSelector = null;
            isColorSelection = false;
            if (hasSelectionEditorState)
            {
                hasSelectionEditorState = false;
                foreach (var entry in selectionVisibility)
                {
                    if (entry.Key == null)
                        continue;
                    entry.Key.forceRenderingOff = entry.Value;
                }

                selectionVisibility.Clear();
                var showObjects = new List<GameObject>();
                var hideObjects = new List<GameObject>();
                var visibility = SceneVisibilityManager.instance;
                foreach (var entry in previousHierarchyVisibility)
                {
                    if (entry.Key == null || visibility.IsHidden(entry.Key) == entry.Value)
                        continue;
                    (entry.Value ? hideObjects : showObjects).Add(entry.Key);
                }
                previousHierarchyVisibility.Clear();
                if (showObjects.Count > 0) visibility.Show(showObjects.ToArray(), false);
                if (hideObjects.Count > 0) visibility.Hide(hideObjects.ToArray(), false);
                Tools.current = previousTool;
                if (previousTool == Tool.Custom && previousToolType != null)
                    UnityEditor.EditorTools.ToolManager.SetActiveTool(previousToolType);
                Tools.hidden = previousToolsHidden;
                Tools.pivotMode = previousPivotMode;
                Tools.pivotRotation = previousPivotRotation;
                foreach (var entry in previousSceneGizmos)
                {
                    if (entry.Key != null)
                        entry.Key.drawGizmos = entry.Value;
                }
                previousSceneGizmos.Clear();
                foreach (var entry in previousSceneCameraModes)
                {
                    if (entry.Key != null)
                        entry.Key.cameraMode = entry.Value;
                }
                previousSceneCameraModes.Clear();
                if (previousSelectionOutline.HasValue)
                    selectionOutlineProperty.SetValue(null, previousSelectionOutline.Value);
                previousSelectionOutline = null;
            }
            if (bakedSkinnedMesh != null)
            {
                DestroyImmediate(bakedSkinnedMesh);
                bakedSkinnedMesh = null;
            }
            SceneView.RepaintAll();
            EditorApplication.RepaintHierarchyWindow();
        }

        private static void StopSelectionOnPlayModeChange(PlayModeStateChange state)
        {
            StopVertexSelection();
        }

        private static void ApplyHierarchyIsolation()
        {
            if (activeVertexSelector == null)
                return;

            var target = activeVertexSelector;
            var stage = UnityEditor.SceneManagement.StageUtility.GetStageHandle(target.gameObject);
            var visibility = SceneVisibilityManager.instance;
            Renderer targetRenderer = target.GetMeshRenderer();
            var showObjects = new List<GameObject>();
            var hideObjects = new List<GameObject>();
            foreach (Transform sceneTransform in Resources.FindObjectsOfTypeAll<Transform>())
            {
                GameObject sceneObject = sceneTransform.gameObject;
                if (!sceneObject.scene.IsValid() || !sceneObject.scene.isLoaded ||
                    UnityEditor.SceneManagement.StageUtility.GetStageHandle(sceneObject) != stage)
                    continue;

                bool hidden = visibility.IsHidden(sceneObject);
                if (!previousHierarchyVisibility.ContainsKey(sceneObject))
                    previousHierarchyVisibility.Add(sceneObject, hidden);
                bool shouldHide = !sceneTransform.IsChildOf(target.transform) &&
                                  (targetRenderer == null || sceneObject != targetRenderer.gameObject);
                if (hidden != shouldHide)
                    (shouldHide ? hideObjects : showObjects).Add(sceneObject);
            }
            if (hideObjects.Count > 0) visibility.Hide(hideObjects.ToArray(), false);
            if (showObjects.Count > 0) visibility.Show(showObjects.ToArray(), false);
            EditorApplication.RepaintHierarchyWindow();
        }

        private static void FinishSelectionDisable()
        {
            VertexTypeCompoment selector = activeVertexSelector;
            if (selector != null && selector.isActiveAndEnabled)
                return;

            StopVertexSelection();
        }

        private static void LockVertexSelectionTools()
        {
            if (activeVertexSelector == null ||
                UnityEditor.SceneManagement.StageUtility.GetCurrentStageHandle() !=
                UnityEditor.SceneManagement.StageUtility.GetStageHandle(activeVertexSelector.gameObject))
            {
                StopVertexSelection();
                return;
            }

            if (!activeVertexSelector.isActiveAndEnabled)
                return;

            Renderer targetRenderer = activeVertexSelector.GetMeshRenderer();
            foreach (var entry in selectionVisibility)
            {
                if (entry.Key != null)
                {
                    bool hidden = entry.Key != targetRenderer &&
                                  !entry.Key.transform.IsChildOf(activeVertexSelector.transform);
                    if (entry.Key.forceRenderingOff != hidden)
                        entry.Key.forceRenderingOff = hidden;
                }
            }

            if (Tools.current != Tool.None)
                Tools.current = Tool.None;
            Tools.hidden = true;
            Tools.pivotMode = previousPivotMode;
            Tools.pivotRotation = previousPivotRotation;
            foreach (SceneView view in SceneView.sceneViews)
            {
                if (view == null)
                    continue;
                if (!previousSceneGizmos.ContainsKey(view))
                    previousSceneGizmos.Add(view, view.drawGizmos);
                if (!previousSceneCameraModes.ContainsKey(view))
                    previousSceneCameraModes.Add(view, view.cameraMode);
                if (view.cameraMode.drawMode != DrawCameraMode.TexturedWire)
                {
                    view.cameraMode = SceneView.GetBuiltinCameraMode(DrawCameraMode.TexturedWire);
                    view.Repaint();
                }
                if (view.drawGizmos)
                {
                    view.drawGizmos = false;
                    view.Repaint();
                }
            }
            if (previousSelectionOutline.HasValue && (bool)selectionOutlineProperty.GetValue(null))
            {
                selectionOutlineProperty.SetValue(null, false);
                SceneView.RepaintAll();
            }
        }

        private Color GetVertexSelectionModeColor()
        {
            return activeVertexSelector == this && !isColorSelection ? Color.green : Color.red;
        }

        private bool IsSelectionTargetRenderer(Renderer renderer)
        {
            return renderer.transform.IsChildOf(transform) || renderer == GetMeshRenderer();
        }

        private static void OnSceneGUI(SceneView sceneView)
        {
            if (activeVertexSelector == null)
            {
                StopVertexSelection();
                return;
            }

            Event currentEvent = Event.current;
            int controlId = GUIUtility.GetControlID("VertexTypeCompoment.Selection".GetHashCode(), FocusType.Passive);
            if (currentEvent.type == EventType.Layout && !currentEvent.alt)
            {
                HandleUtility.AddDefaultControl(controlId);
            }

            if (currentEvent.type == EventType.KeyDown && currentEvent.keyCode == KeyCode.Escape)
            {
                StopVertexSelection();
                currentEvent.Use();
                return;
            }

            if (!currentEvent.alt && currentEvent.type == EventType.MouseDown &&
                currentEvent.button == 0 &&
                activeVertexSelector.TryPickTriangle(HandleUtility.GUIPointToWorldRay(currentEvent.mousePosition),
                    out int vertexA, out int vertexB, out int vertexC))
            {
                currentEvent.Use();

                if (isColorSelection)
                {
                    activeVertexSelector.PaintTriangleVertices(vertexA, vertexB, vertexC);
                    return;
                }

                Undo.IncrementCurrentGroup();
                Undo.RegisterCompleteObjectUndo(activeVertexSelector, "Toggle Emission Vertex");

                activeVertexSelector.ExpandSelection(vertexA, vertexB, vertexC);
                var emission = new HashSet<int>(activeVertexSelector.emissionVertexIndices);
                bool allSelected = emission.IsSupersetOf(activeVertexSelector.selectionVertices);
                if (allSelected)
                    emission.ExceptWith(activeVertexSelector.selectionVertices);
                else
                    emission.UnionWith(activeVertexSelector.selectionVertices);
                activeVertexSelector.emissionVertexIndices.Clear();
                activeVertexSelector.emissionVertexIndices.AddRange(emission);

                activeVertexSelector.NormalizeEmissionVertexIndices();
                activeVertexSelector.ApplyEmissionColorsToMesh();
                activeVertexSelector.CacheStateHashes();
                EditorUtility.SetDirty(activeVertexSelector);
                PrefabUtility.RecordPrefabInstancePropertyModifications(activeVertexSelector);
                SceneView.RepaintAll();
            }
        }

        private static void DrawVertexSelectionPreview(SceneView sceneView)
        {
            if (activeVertexSelector == null)
                return;

            Event currentEvent = Event.current;
            if (currentEvent.type == EventType.MouseMove || currentEvent.type == EventType.MouseDrag)
                sceneView.Repaint();
            if (currentEvent.type != EventType.Repaint || currentEvent.alt || EditorWindow.mouseOverWindow != sceneView)
                return;

            Ray ray = HandleUtility.GUIPointToWorldRay(currentEvent.mousePosition);
            if (!activeVertexSelector.TryPickTriangle(ray, out int a, out int b, out int c))
                return;

            List<Vector3> vertices = activeVertexSelector.sceneVertices;
            Transform modelTransform = activeVertexSelector.GetMeshTransform();
            activeVertexSelector.ExpandSelection(a, b, c);
            if (activeVertexSelector.previewVertices.Length != vertices.Count)
                activeVertexSelector.previewVertices = new Vector3[vertices.Count];
            vertices.CopyTo(activeVertexSelector.previewVertices);
            using (new Handles.DrawingScope(Color.cyan, modelTransform.localToWorldMatrix))
                Handles.DrawLines(activeVertexSelector.previewVertices, activeVertexSelector.previewLineIndices);
        }

        private Mesh GetSceneMesh()
        {
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            if (skinnedMeshRenderer != null)
            {
                if (skinnedMeshRenderer.sharedMesh == null)
                    return null;

                if (bakedSkinnedMesh == null)
                {
                    bakedSkinnedMesh = new Mesh { hideFlags = HideFlags.HideAndDontSave };
                }

                skinnedMeshRenderer.BakeMesh(bakedSkinnedMesh, true);
                if (bakedSkinnedMesh.vertexCount != skinnedMeshRenderer.sharedMesh.vertexCount)
                    return null;
                return bakedSkinnedMesh;
            }

            return GetSourceMesh();
        }

        private void ExpandSelection(int a, int b, int c)
        {
            Mesh topologySource = sourceMesh != null ? sourceMesh : GetSourceMesh();
            if (selectionTopology == null || selectionTopology.mesh != topologySource)
            {
                selectionTopology = new SelectionTopology(topologySource);
                lastSelection = (-1, -1, -1, VertexSelectionShape.Triangle);
                visitedTriangles.Clear();
            }
            var key = (a, b, c, selectionMode);
            if (lastSelection.Equals(key))
                return;
            if (!selectionTopology.triangleLookup.TryGetValue((a, b, c), out int seed))
                return;
            bool isIsland = selectionMode == VertexSelectionShape.MeshIsland || selectionMode == VertexSelectionShape.UVSeam;
            if (isIsland && lastSelection.mode == selectionMode && visitedTriangles.Contains(seed))
            {
                lastSelection = key;
                return;
            }
            lastSelection = key;
            selectionTriangles.Clear();
            selectionVertices.Clear();
            visitedTriangles.Clear();
            int[] triangles = selectionTopology.triangles;

            selectionTriangles.Add(seed);
            if (selectionMode == VertexSelectionShape.Square)
            {
                int partner = selectionTopology.FindQuadPartner(seed);
                if (partner >= 0)
                    selectionTriangles.Add(partner);
            }
            else if (selectionMode != VertexSelectionShape.Triangle)
            {
                visitedTriangles.Add(seed);
                var links = selectionMode == VertexSelectionShape.UVSeam
                    ? selectionTopology.uvLinks : selectionTopology.meshLinks;
                for (int i = 0; i < selectionTriangles.Count; i++)
                    foreach (int neighbor in links[selectionTriangles[i]])
                        if (visitedTriangles.Add(neighbor))
                            selectionTriangles.Add(neighbor);
            }
            previewEdges.Clear();
            foreach (int triangle in selectionTriangles)
                for (int corner = 0; corner < 3; corner++)
                {
                    int first = triangles[triangle * 3 + corner];
                    int second = triangles[triangle * 3 + (corner + 1) % 3];
                    selectionVertices.Add(first);
                    previewEdges.Add(first < second ? (first, second) : (second, first));
                }
            if (previewLineIndices.Length != previewEdges.Count * 2)
                previewLineIndices = new int[previewEdges.Count * 2];
            int edgeIndex = 0;
            foreach (var edge in previewEdges)
            {
                previewLineIndices[edgeIndex++] = edge.a;
                previewLineIndices[edgeIndex++] = edge.b;
            }
        }

        private sealed class SelectionTopology
        {
            public readonly Mesh mesh;
            public readonly int[] triangles;
            public readonly List<int>[] meshLinks;
            public readonly List<int>[] uvLinks;
            public readonly Dictionary<(int, int, int), int> triangleLookup = new Dictionary<(int, int, int), int>();
            private readonly Vector3[] positions;
            private readonly int[] welded;

            public SelectionTopology(Mesh source)
            {
                mesh = source;
                triangles = source.triangles;
                positions = source.vertices;
                Vector2[] uv = source.uv;
                welded = new int[positions.Length];
                var ids = new Dictionary<Vector3, int>();
                for (int i = 0; i < positions.Length; i++)
                {
                    if (!ids.TryGetValue(positions[i], out int id))
                    { id = ids.Count; ids.Add(positions[i], id); }
                    welded[i] = id;
                }
                int count = triangles.Length / 3;
                meshLinks = new List<int>[count];
                uvLinks = new List<int>[count];
                var edges = new Dictionary<(int, int), List<(int triangle, int a, int b)>>();
                for (int t = 0; t < count; t++)
                {
                    triangleLookup.TryAdd((triangles[t * 3], triangles[t * 3 + 1], triangles[t * 3 + 2]), t);
                    meshLinks[t] = new List<int>();
                    uvLinks[t] = new List<int>();
                    for (int corner = 0; corner < 3; corner++)
                    {
                        int a = triangles[t * 3 + corner], b = triangles[t * 3 + (corner + 1) % 3];
                        if (welded[a] == welded[b]) continue;
                        if (welded[a] > welded[b]) { int swap = a; a = b; b = swap; }
                        var key = (welded[a], welded[b]);
                        if (!edges.TryGetValue(key, out var uses))
                        { uses = new List<(int, int, int)>(); edges.Add(key, uses); }
                        uses.Add((t, a, b));
                    }
                }
                foreach (var uses in edges.Values)
                {
                    if (uses.Count != 2 || uses[0].triangle == uses[1].triangle) continue;
                    var first = uses[0]; var second = uses[1];
                    meshLinks[first.triangle].Add(second.triangle);
                    meshLinks[second.triangle].Add(first.triangle);
                    if (uv.Length == positions.Length && uv[first.a].Equals(uv[second.a]) && uv[first.b].Equals(uv[second.b]))
                    {
                        uvLinks[first.triangle].Add(second.triangle);
                        uvLinks[second.triangle].Add(first.triangle);
                    }
                }
            }

            public int FindQuadPartner(int seed)
            {
                int best = -1;
                float bestLength = 0f;
                foreach (int neighbor in meshLinks[seed])
                {
                    int sharedA = -1, sharedB = -1, sharedCount = 0;
                    int oppositeA = -1, oppositeB = -1;
                    for (int i = 0; i < 3; i++)
                    {
                        int a = triangles[seed * 3 + i];
                        bool found = false;
                        for (int j = 0; j < 3; j++)
                            found |= welded[a] == welded[triangles[neighbor * 3 + j]];
                        if (found)
                        {
                            if (sharedCount++ == 0) sharedA = a; else sharedB = a;
                        }
                        else oppositeA = a;
                    }
                    for (int j = 0; j < 3; j++)
                    {
                        int b = triangles[neighbor * 3 + j];
                        bool found = false;
                        for (int i = 0; i < 3; i++) found |= welded[b] == welded[triangles[seed * 3 + i]];
                        if (!found) oppositeB = b;
                    }
                    if (sharedCount != 2 || oppositeA < 0 || oppositeB < 0) continue;
                    Vector3 p = positions[sharedA], q = positions[sharedB];
                    Vector3 r = positions[oppositeA], s = positions[oppositeB];
                    Vector3 n1 = Vector3.Cross(q - p, r - p), n2 = Vector3.Cross(q - p, s - p);
                    if (n1.sqrMagnitude == 0f || n2.sqrMagnitude == 0f ||
                        Vector3.Dot(n1.normalized, n2.normalized) > -0.999f ||
                        Vector3.Dot(Vector3.Cross(s - r, p - r), Vector3.Cross(s - r, q - r)) >= 0f)
                        continue;
                    float length = (q - p).sqrMagnitude;
                    if (length < Mathf.Max(Mathf.Max((r - p).sqrMagnitude, (r - q).sqrMagnitude),
                            Mathf.Max((s - p).sqrMagnitude, (s - q).sqrMagnitude))) continue;
                    if (length > bestLength) { bestLength = length; best = neighbor; }
                }
                return best;
            }
        }

        private bool TryPickTriangle(Ray worldRay, out int vertexA, out int vertexB, out int vertexC)
        {
            Mesh mesh = GetSceneMesh();
            SkinnedMeshRenderer skinnedMeshRenderer = GetSkinnedMeshRenderer();
            Mesh topologyMesh = skinnedMeshRenderer != null ? GetSourceMesh() : mesh;
            if (mesh == null || topologyMesh == null || !EnsureMeshReadable(topologyMesh))
            {
                vertexA = vertexB = vertexC = -1;
                return false;
            }

            Matrix4x4 worldToLocal = GetMeshTransform().worldToLocalMatrix;
            Vector3 direction = worldToLocal.MultiplyVector(worldRay.direction);
            Ray localRay = new Ray(worldToLocal.MultiplyPoint3x4(worldRay.origin), direction.normalized);
            vertexA = vertexB = vertexC = -1;
            if (direction.sqrMagnitude == 0f || !mesh.bounds.IntersectRay(localRay))
                return false;
            mesh.GetVertices(sceneVertices);
            Mesh topologySource = sourceMesh != null ? sourceMesh : topologyMesh;
            if (selectionTopology == null || selectionTopology.mesh != topologySource)
            {
                selectionTopology = new SelectionTopology(topologySource);
                lastSelection = (-1, -1, -1, VertexSelectionShape.Triangle);
                visitedTriangles.Clear();
            }
            int[] triangles = selectionTopology.triangles;
            float closestDistance = float.MaxValue;
            vertexA = vertexB = vertexC = -1;

            for (int triangleIndex = 0; triangleIndex < triangles.Length; triangleIndex += 3)
            {
                int candidateA = triangles[triangleIndex];
                int candidateB = triangles[triangleIndex + 1];
                int candidateC = triangles[triangleIndex + 2];
                if (RayIntersectsTriangle(localRay, sceneVertices[candidateA], sceneVertices[candidateB], sceneVertices[candidateC], out float distance) &&
                    distance < closestDistance)
                {
                    closestDistance = distance;
                    vertexA = candidateA;
                    vertexB = candidateB;
                    vertexC = candidateC;
                }
            }

            return vertexA >= 0;
        }

        private static bool RayIntersectsTriangle(Ray ray, Vector3 vertexA, Vector3 vertexB, Vector3 vertexC, out float distance)
        {
            const float epsilon = 0.000001f;
            Vector3 edgeAB = vertexB - vertexA;
            Vector3 edgeAC = vertexC - vertexA;
            Vector3 pVector = Vector3.Cross(ray.direction, edgeAC);
            float determinant = Vector3.Dot(edgeAB, pVector);
            float area = Vector3.Cross(edgeAB, edgeAC).magnitude;
            if (area <= 0f || Mathf.Abs(determinant) <= epsilon * area)
            {
                distance = 0f;
                return false;
            }

            float inverseDeterminant = 1f / determinant;
            Vector3 tVector = ray.origin - vertexA;
            float u = Vector3.Dot(tVector, pVector) * inverseDeterminant;
            if (u < 0f || u > 1f)
            {
                distance = 0f;
                return false;
            }

            Vector3 qVector = Vector3.Cross(tVector, edgeAB);
            float v = Vector3.Dot(ray.direction, qVector) * inverseDeterminant;
            if (v < 0f || u + v > 1f)
            {
                distance = 0f;
                return false;
            }

            distance = Vector3.Dot(edgeAC, qVector) * inverseDeterminant;
            return distance >= 0f;
        }
#endif

    }
}
