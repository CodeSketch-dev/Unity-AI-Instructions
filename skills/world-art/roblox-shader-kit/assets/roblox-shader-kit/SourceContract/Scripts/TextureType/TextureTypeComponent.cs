using UnityEngine;
using Sirenix.OdinInspector;

namespace Base_VanHuy
{
    [ExecuteAlways]
    public partial class TextureTypeComponent : MonoBehaviour
    {
        private sealed class CachedMaterial
        {
            public Material material;
            public int referenceCount;
        }

        private static readonly System.Collections.Generic.Dictionary<string, CachedMaterial> MaterialVariants =
            new System.Collections.Generic.Dictionary<string, CachedMaterial>();

        [System.Serializable]
        private class MaterialBackup
        {
            public Renderer renderer;
            public Material[] originalMaterials;
            public Material[] clonedMaterials;
        }

        [System.NonSerialized] private MaterialBackup[] materialBackups;
        [System.NonSerialized] private string materialVariantKey;

        public Material[] Materials
        {
            get
            {
                var renderer = GetComponent<Renderer>();
                return renderer != null ? renderer.sharedMaterials : System.Array.Empty<Material>();
            }
        }

        private int MaterialInstanceCount => materialBackups?.Length ?? 0;
        
        public bool SolidColorEnabled
        {
            get => true;
            set { }
        }

        public Color SolidColor
        {
            get => solidColor;
            set
            {
                solidColor = value;
                RefreshMaterialsIfPlaying();
#if UNITY_EDITOR
                if (!Application.isPlaying)
                    QueueMaterialPreviewUpdate();
#endif
            }
        }

        public bool IsTransparent
        {
            get => isTransparent;
            set { isTransparent = value; RefreshMaterialsIfPlaying(); }
        }

        public float Alpha
        {
            get => solidColor.a;
            set
            {
                solidColor.a = Mathf.Clamp01(value);
                RefreshMaterialsIfPlaying();
#if UNITY_EDITOR
                if (!Application.isPlaying)
                    QueueMaterialPreviewUpdate();
#endif
            }
        }

        private void RefreshMaterialsIfPlaying()
        {
            if (!Application.isPlaying || !isActiveAndEnabled)
                return;

            CreateAndAssignMaterialClones();
        }

        private Material GetMaterialTemplate()
        {
            return textureDataAsset != null
                ? isTransparent ? textureDataAsset.TransparentMaterial : textureDataAsset.OpaqueMaterial
                : null;
        }

        [SerializeField, HideInInspector]
        private Color solidColor = Color.white;

        [SerializeField, HideInInspector]
        private bool isTransparent;

        [SerializeField, HideInInspector]
        private bool applyTextureData = false;

        [SerializeField, HideInInspector]
        private bool shadowCastingInitialized;

        [SerializeField, ReadOnly]
        private TextureDataAsset textureDataAsset;

        [SerializeField, HideInInspector]
        private Texture2D albedoTexture;

        [SerializeField, HideInInspector]
        private Texture2D legoDetailTexture;

        [SerializeField, HideInInspector]
        private Texture2D legoNormalTexture;

        [SerializeField, HideInInspector]
        private bool isAlbedoMovement;

        [SerializeField, HideInInspector]
        private bool isLegoDetail;

        [SerializeField, HideInInspector]
        private bool isCheckerDetail;

        [SerializeField, HideInInspector]
        private float checkerTiling = 8f;

        [SerializeField, HideInInspector]
        private float legoTiling = 1f;

        [SerializeField, HideInInspector]
        private Vector2 movementXY = new Vector2(0.1f, 0f);

        [SerializeField, HideInInspector]
        private bool enableEmission;

        [SerializeField, HideInInspector]
        private float emissionStrength = 3f;

        public bool EmissionEnabled
        {
            get => enableEmission;
            set
            {
                if (enableEmission == value)
                    return;

                enableEmission = value;
                RefreshMaterialsIfPlaying();
#if UNITY_EDITOR
                if (!Application.isPlaying)
                    QueueMaterialPreviewUpdate();
#endif
            }
        }
        public float EmissionStrength
        {
            get => emissionStrength;
            set
            {
                emissionStrength = Mathf.Clamp(value, 1f, 10f);
                RefreshMaterialsIfPlaying();
#if UNITY_EDITOR
                if (!Application.isPlaying)
                    QueueMaterialPreviewUpdate();
#endif
            }
        }

        private bool ShouldPreviewMaterialInstance => isActiveAndEnabled;

        private void UpdateMaterialPreview()
        {
            if (Application.isPlaying)
                return;

            if (!ShouldPreviewMaterialInstance)
            {
                RevertToOriginalMaterialsInternal();
                return;
            }

            CreateAndAssignMaterialClones();
        }

        private void ApplyMaterialSettings(Material material)
        {
            if (isTransparent)
                SetMaterialTransparent(material);
            else
                SetMaterialOpaque(material);

            SetMaterialKeyword(material, "_IS_TEXTURE", applyTextureData);
            SetMaterialKeyword(material, "_IS_ALBEDO_MOVEMENT", applyTextureData && isAlbedoMovement);
            SetMaterialKeyword(material, "_IS_LEGODETAIL", applyTextureData && isLegoDetail);
            SetMaterialKeyword(material, "_IS_CHECKERDETAIL", applyTextureData && isCheckerDetail);
            ApplyEmission(material);
            var color = solidColor;
            color.a = isTransparent ? color.a : 1f;
            SetMaterialColor(material, color);
            SetMaterialTexture(material, "_Albedo", albedoTexture);
            SetMaterialTexture(material, "_LegoDetail", legoDetailTexture != null ? legoDetailTexture : textureDataAsset?.LegoDetailTexture);
            SetMaterialTexture(material, "_LegoNormal", legoNormalTexture != null ? legoNormalTexture : textureDataAsset?.LegoNormalTexture);
            SetMaterialTexture(material, "_CheckerDetail", textureDataAsset?.CheckerDetailTexture);
            SetMaterialFloat(material, "_IS_TEXTURE", applyTextureData ? 1f : 0f);
            SetMaterialFloat(material, "_IS_ALBEDO_MOVEMENT", applyTextureData && isAlbedoMovement ? 1f : 0f);
            SetMaterialFloat(material, "_IS_LEGODETAIL", applyTextureData && isLegoDetail ? 1f : 0f);
            SetMaterialFloat(material, "_IS_CHECKERDETAIL", applyTextureData && isCheckerDetail ? 1f : 0f);
            SetMaterialFloat(material, "_Checker_Tiling", checkerTiling);
            SetMaterialFloat(material, "_Lego_Tiling", legoTiling);
            SetMaterialVector(material, "_Movement_X_Y", movementXY);
            SetMaterialFloat(material, "_EMISSION", enableEmission ? 1f : 0f);
            SetMaterialFloat(material, "_Emission_Strength", emissionStrength);
        }

        private void ApplyEmission(Material material)
        {
            SetMaterialKeyword(material, "_EMISSION", enableEmission);
        }

        private void SetMaterialTexture(Material material, string propertyName, Texture texture)
        {
            if (material.HasProperty(propertyName))
                material.SetTexture(propertyName, applyTextureData ? texture : null);
        }

        private static void SetMaterialKeyword(Material material, string keywordName, bool isEnabled)
        {
            if (isEnabled)
                material.EnableKeyword(keywordName);
            else
                material.DisableKeyword(keywordName);
        }

        private static void SetMaterialFloat(Material material, string propertyName, float value)
        {
            if (material.HasProperty(propertyName))
                material.SetFloat(propertyName, value);
        }

        private static void SetMaterialVector(Material material, string propertyName, Vector2 value)
        {
            if (material.HasProperty(propertyName))
                material.SetVector(propertyName, value);
        }

        private static void SetMaterialColor(Material material, Color color)
        {
            if (material.HasProperty("_BaseColor"))
                material.SetColor("_BaseColor", color);

            if (material.HasProperty("_Color"))
                material.SetColor("_Color", color);
        }

        private static void SetMaterialTransparent(Material material)
        {
            if (material.HasProperty("_Surface"))
            {
                material.SetFloat("_Surface", 1f);
                if (material.HasProperty("_Blend"))
                    material.SetFloat("_Blend", 0f);
                material.SetOverrideTag("RenderType", "Transparent");
                material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                material.SetInt("_SrcBlendAlpha", (int)UnityEngine.Rendering.BlendMode.One);
                material.SetInt("_DstBlendAlpha", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                material.SetInt("_ZWrite", 0);
                material.DisableKeyword("_ALPHATEST_ON");
                material.EnableKeyword("_ALPHAPREMULTIPLY_ON");
                material.DisableKeyword("_ALPHAMODULATE_ON");
                material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                material.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            }
            else if (material.HasProperty("_Mode"))
            {
                material.SetFloat("_Mode", 2f);
                material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                material.SetInt("_ZWrite", 0);
                material.DisableKeyword("_ALPHATEST_ON");
                material.EnableKeyword("_ALPHABLEND_ON");
                material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                material.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            }
        }

        private static void SetMaterialOpaque(Material material)
        {
            if (material.HasProperty("_Surface"))
            {
                material.SetFloat("_Surface", 0f);
                material.SetOverrideTag("RenderType", "");
                material.SetInt("_ZWrite", 1);
                material.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
                material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                material.DisableKeyword("_ALPHAMODULATE_ON");
                material.renderQueue = -1;
            }
            else if (material.HasProperty("_Mode"))
            {
                material.SetFloat("_Mode", 0f);
                material.SetInt("_ZWrite", 1);
                material.DisableKeyword("_ALPHABLEND_ON");
                material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                material.renderQueue = -1;
            }
        }

        private void OnEnable()
        {
            InitializeShadowCasting();

            if (Application.isPlaying)
            {
                RevertToOriginalMaterialsInternal();
                CreateAndAssignMaterialClones();
            }
#if UNITY_EDITOR
            else
            {
                var assignedTextureDataAsset = AssignDefaultTextureDataAssetIfNeeded();
                var assignedLegoTextures = AssignDefaultLegoTexturesIfNeeded();
                if (assignedTextureDataAsset || assignedLegoTextures)
                    MarkEditorDirty();
                UpdateMaterialPreview();
            }
#endif
        }

        private void OnDisable()
        {
#if UNITY_EDITOR
            ClearInspectorColorPreview();
#endif
            RevertToOriginalMaterialsInternal();
        }

        private void Update()
        {
            if (Application.isPlaying || HasValidClones())
                return;

            CreateAndAssignMaterialClones();
        }

        private void Reset()
        {
            applyTextureData = false;
            shadowCastingInitialized = false;
            InitializeShadowCasting();

#if UNITY_EDITOR
            AssignDefaultTextureDataAssetIfNeeded();
            AssignDefaultLegoTexturesIfNeeded();
#endif
        }

        private void InitializeShadowCasting()
        {
            if (shadowCastingInitialized)
                return;

            foreach (var targetRenderer in GetComponents<Renderer>())
                targetRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

            shadowCastingInitialized = true;
        }

        private void OnValidate()
        {
#if UNITY_EDITOR
            var assignedDefaultTextureDataAsset = AssignDefaultTextureDataAssetIfNeeded();
            var assignedDefaultLegoTextures = AssignDefaultLegoTexturesIfNeeded();
            if (assignedDefaultTextureDataAsset || assignedDefaultLegoTextures)
                MarkEditorDirty();
#endif
        }

        private void OnDestroy()
        {
#if UNITY_EDITOR
            ClearInspectorColorPreview();
#endif
            RestoreOriginalMaterials();
            DestroyMaterialClones();
        }

        public void CreateAndAssignMaterialClones()
        {
            var materialTemplate = GetMaterialTemplate();
            if (materialTemplate == null)
            {
                var materialTypeName = isTransparent ? "transparent" : "opaque";
                Debug.LogError($"TextureTypeComponent requires a {materialTypeName} material template.", this);
                return;
            }

            var variantKey = BuildMaterialVariantKey(materialTemplate);
            if (HasValidClones() && materialVariantKey == variantKey)
                return;

            if (materialBackups != null)
            {
                RestoreOriginalMaterials();
                DestroyMaterialClones();
            }

            var renderers = GetComponents<Renderer>();
            if (renderers.Length == 0)
                return;

            var sharedMaterial = AcquireMaterialVariant(variantKey, materialTemplate);
            materialVariantKey = variantKey;

            materialBackups = new MaterialBackup[renderers.Length];
            for (var rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                var targetRenderer = renderers[rendererIndex];
                var sourceMaterials = targetRenderer.sharedMaterials;
                var backup = new MaterialBackup
                {
                    renderer = targetRenderer,
                    originalMaterials = sourceMaterials,
                    clonedMaterials = new Material[System.Math.Max(1, sourceMaterials.Length)]
                };
                materialBackups[rendererIndex] = backup;

                for (var materialIndex = 0; materialIndex < backup.clonedMaterials.Length; materialIndex++)
                    backup.clonedMaterials[materialIndex] = sharedMaterial;

                targetRenderer.sharedMaterials = backup.clonedMaterials;
            }
        }

        private string BuildMaterialVariantKey(Material materialTemplate)
        {
            var color = solidColor;
            color.a = isTransparent ? color.a : 1f;
            var textureEnabled = applyTextureData;
            var movementEnabled = textureEnabled && isAlbedoMovement;
            var legoDetailEnabled = textureEnabled && isLegoDetail;
            var checkerDetailEnabled = textureEnabled && isCheckerDetail;
            return string.Join("|",
                GetObjectId(materialTemplate), color.r.ToString("R"), color.g.ToString("R"), color.b.ToString("R"), color.a.ToString("R"),
                textureEnabled, textureEnabled ? GetObjectId(albedoTexture) : 0,
                legoDetailEnabled ? GetObjectId(legoDetailTexture != null ? legoDetailTexture : textureDataAsset?.LegoDetailTexture) : 0,
                legoDetailEnabled ? GetObjectId(legoNormalTexture != null ? legoNormalTexture : textureDataAsset?.LegoNormalTexture) : 0,
                checkerDetailEnabled ? GetObjectId(textureDataAsset?.CheckerDetailTexture) : 0,
                movementEnabled, legoDetailEnabled, checkerDetailEnabled,
                checkerDetailEnabled ? checkerTiling.ToString("R") : "0", legoDetailEnabled ? legoTiling.ToString("R") : "0",
                movementEnabled ? movementXY.x.ToString("R") : "0", movementEnabled ? movementXY.y.ToString("R") : "0",
                enableEmission, enableEmission ? emissionStrength.ToString("R") : "0");
        }

        private static int GetObjectId(Object value)
        {
            return value != null ? value.GetInstanceID() : 0;
        }

        private Material AcquireMaterialVariant(string variantKey, Material materialTemplate)
        {
            if (MaterialVariants.TryGetValue(variantKey, out var cachedMaterial) && cachedMaterial.material != null)
            {
                cachedMaterial.referenceCount++;
                return cachedMaterial.material;
            }

            var material = new Material(materialTemplate)
            {
                name = materialTemplate.name + " (TextureType Shared Variant)",
                enableInstancing = true
            };
            ApplyMaterialSettings(material);

#if UNITY_EDITOR
            material.hideFlags = HideFlags.DontSaveInEditor | HideFlags.DontSaveInBuild;
#endif

            MaterialVariants[variantKey] = new CachedMaterial { material = material, referenceCount = 1 };
            return material;
        }

        public void RestoreOriginalMaterials()
        {
            if (materialBackups == null)
                return;

            foreach (var backup in materialBackups)
            {
                if (backup != null && backup.renderer != null && backup.originalMaterials != null)
                    backup.renderer.sharedMaterials = backup.originalMaterials;
            }
        }

        [ContextMenu("Revert to Original Materials")]
        public void RevertToOriginalMaterials()
        {
            if (ShouldPreviewMaterialInstance)
            {
                Debug.LogWarning("Disable all Apply options before reverting materials manually.", this);
                return;
            }

            RevertToOriginalMaterialsInternal(revertPrefabOverrides: true);
        }

        private void RevertToOriginalMaterialsInternal(bool revertPrefabOverrides = false)
        {
            RestoreOriginalMaterials();

#if UNITY_EDITOR
            if (revertPrefabOverrides)
                RevertMaterialPrefabOverrides();
#endif

            DestroyMaterialClones();
        }

        private bool HasValidClones()
        {
            if (materialBackups == null || materialBackups.Length == 0)
                return false;

            foreach (var backup in materialBackups)
            {
                if (backup == null || backup.renderer == null || backup.clonedMaterials == null ||
                    backup.renderer.sharedMaterials.Length != backup.clonedMaterials.Length)
                    return false;

                for (var materialIndex = 0; materialIndex < backup.clonedMaterials.Length; materialIndex++)
                {
                    if (backup.renderer.sharedMaterials[materialIndex] != backup.clonedMaterials[materialIndex])
                        return false;
                }
            }

            return true;
        }

        private void DestroyMaterialClones()
        {
            if (materialBackups == null)
                return;

            if (!string.IsNullOrEmpty(materialVariantKey) && MaterialVariants.TryGetValue(materialVariantKey, out var cachedMaterial))
            {
                cachedMaterial.referenceCount--;
                if (cachedMaterial.referenceCount <= 0)
                {
                    MaterialVariants.Remove(materialVariantKey);
                    if (Application.isPlaying)
                        Destroy(cachedMaterial.material);
                    else
                        DestroyImmediate(cachedMaterial.material);
                }
            }

            materialBackups = null;
            materialVariantKey = null;
        }

    }
}
