using Sirenix.OdinInspector;
using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Base_VanHuy
{
    public partial class VertexTypeCompoment
    {
        public enum MetalFinish { None, Gold, Silver, Rainbow, Cosmic }

        [SerializeField, EnumToggleButtons, LabelText("Metal Mode"), PropertyOrder(-100)]
        private MetalFinish metalFinish;
        [SerializeField, ReadOnly]
        private TextureDataAsset textureDataAsset;
        public Material MetalMaterial => textureDataAsset != null ? textureDataAsset.MetalMaterial : null;
        [SerializeField, ShowIf("HasMetalFinish"), Range(0f, 1f), LabelText("Metal Blend")]
        private float metalBlend = 1f;

        [SerializeField, ShowIf("HasRainbowFinish"), Range(-2f, 2f), LabelText("Rainbow Speed")]
        private float rainbowSpeed = 0.5f;
        [SerializeField, ShowIf("HasRainbowFinish"), Range(0.1f, 5f), LabelText("Rainbow Scale")]
        private float rainbowScale = 1f;
        [SerializeField, ShowIf("HasRainbowFinish"), Range(0f, 360f), LabelText("Rainbow Rotation")]
        [Tooltip("Rotate rainbow bands around the local X axis, in degrees (0–360).")]
        private float rainbowRotation = 45f;

        [SerializeField, ShowIf("HasCosmicFinish"), Range(0f, 10f), LabelText("Cosmic Brightness")]
        private float cosmicBrightness = 3f;
        [SerializeField, ShowIf("HasCosmicFinish"), Range(0.1f, 1f), LabelText("Cosmic Scale")]
        [Tooltip("Texture density. Higher values make cosmic details smaller.")]
        private float cosmicScale = 0.3f;
        // Keep serialized speed in cycles per second so existing prefabs retain their motion.
        [SerializeField, ShowIf("HasCosmicFinish"), Range(0.01f, 1f), LabelText("Cosmic Speed")]
        private float cosmicSpeed = 0.03f;

        private static readonly int MetalTintId = Shader.PropertyToID("_Tint");
        private static readonly int MetalBlendId = Shader.PropertyToID("_BlendStrength");
        private static readonly int RainbowStrengthId = Shader.PropertyToID("_RainbowStrength");
        private static readonly int RainbowSpeedId = Shader.PropertyToID("_RainbowSpeed");
        private static readonly int RainbowScaleId = Shader.PropertyToID("_RainbowScale");
        private static readonly int RainbowRotationId = Shader.PropertyToID("_RainbowRotation");
        private static readonly int RainbowBoundsId = Shader.PropertyToID("_RainbowBounds");
        private static readonly int CosmicCubemapId = Shader.PropertyToID("_CosmicCubemap");
        private static readonly int CosmicStrengthId = Shader.PropertyToID("_CosmicStrength");
        private static readonly int CosmicBrightnessId = Shader.PropertyToID("_CosmicBrightness");
        private static readonly int CosmicScaleId = Shader.PropertyToID("_CosmicScale");
        private static readonly int CosmicSpeedId = Shader.PropertyToID("_CosmicSpeed");
        private GameObject metalOverlayObject;
        private Renderer metalOverlayRenderer;
        private Renderer metalSourceRenderer;
        private MaterialPropertyBlock metalPropertyBlock;
        private Material appliedMetalMaterial;
        private int appliedMetalSubmeshCount;

        private bool HasMetalFinish => metalFinish != MetalFinish.None;
        private bool HasRainbowFinish => metalFinish == MetalFinish.Rainbow;
        private bool HasCosmicFinish => metalFinish == MetalFinish.Cosmic;
        private bool HasAnimatedMetalFinish => HasRainbowFinish || HasCosmicFinish;


        public Cubemap CosmicCubemap => textureDataAsset != null ? textureDataAsset.CosmicCubemap : null;

        [ShowInInspector, ShowIf("HasCosmicFinish"), Range(-200f, 200f), LabelText("Cosmic Speed")]
        [Tooltip("Speed uses a 100x input scale: 1 = 0.01 cycles per second. Zero stops drift; negative reverses it.")]
        public float CosmicSpeed
        {
            get => cosmicSpeed * 100f;
            set { cosmicSpeed = Mathf.Clamp(value, -200f, 200f) / 100f; ApplyMetalAppearance(); }
        }

        public float CosmicScale
        {
            get => cosmicScale;
            set
            {
                cosmicScale = Mathf.Clamp(value, 0.1f, 1f);
                ApplyMetalAppearance();
            }
        }

        public float CosmicBrightness
        {
            get => cosmicBrightness;
            set { cosmicBrightness = Mathf.Clamp(value, 0f, 10f); ApplyMetalAppearance(); }
        }

        public float RainbowSpeed
        {
            get => rainbowSpeed;
            set { rainbowSpeed = Mathf.Clamp(value, -2f, 2f); ApplyMetalAppearance(); }
        }

        public float RainbowScale
        {
            get => rainbowScale;
            set { rainbowScale = Mathf.Clamp(value, 0.1f, 5f); ApplyMetalAppearance(); }
        }

        public float RainbowRotation
        {
            get => rainbowRotation;
            set { rainbowRotation = Mathf.Clamp(value, 0f, 360f); ApplyMetalAppearance(); }
        }

#if UNITY_EDITOR
        private bool rainbowPreviewSubscribed;
        private double nextRainbowPreviewTime;

        private void UpdateRainbowEditorPreview()
        {
            if (Application.isPlaying || !isActiveAndEnabled || !HasAnimatedMetalFinish)
            {
                StopRainbowEditorPreview();
                return;
            }
            if (EditorApplication.timeSinceStartup < nextRainbowPreviewTime)
                return;
            nextRainbowPreviewTime = EditorApplication.timeSinceStartup + 1.0 / 30.0;
            EditorApplication.QueuePlayerLoopUpdate();
            SceneView.RepaintAll();
        }

        private void StopRainbowEditorPreview()
        {
            EditorApplication.update -= UpdateRainbowEditorPreview;
            rainbowPreviewSubscribed = false;
        }
#endif

        public MetalFinish Finish
        {
            get => metalFinish;
            set { metalFinish = value; ApplyMetalAppearance(); }
        }

        public TextureDataAsset TextureData
        {
            get => textureDataAsset;
            set { textureDataAsset = value; ApplyMetalAppearance(); }
        }

        public float MetalBlend
        {
            get => metalBlend;
            set { metalBlend = Mathf.Clamp01(value); ApplyMetalAppearance(); }
        }

        private void LateUpdate()
        {
            // Mesh painting and skin animation can change after the Inspector update.
            if (HasMetalFinish || metalOverlayObject != null)
                ApplyMetalAppearance();
        }

        private void ApplyMetalAppearance()
        {
            if (!isActiveAndEnabled)
                return;
#if UNITY_EDITOR
            if (textureDataAsset == null)
            {
                textureDataAsset = AssetDatabase.LoadAssetAtPath<TextureDataAsset>(
                    "Assets/vanhuy_probloxengine/0_Asset Library/Shader Library/Textures/TextureDataAsset.asset");
                if (textureDataAsset == null)
                {
                    var assetGuids = AssetDatabase.FindAssets("t:TextureDataAsset");
                    if (assetGuids.Length > 0)
                        textureDataAsset = AssetDatabase.LoadAssetAtPath<TextureDataAsset>(
                            AssetDatabase.GUIDToAssetPath(assetGuids[0]));
                }
                if (textureDataAsset != null && !Application.isPlaying)
                    EditorUtility.SetDirty(this);
            }
#endif
            var metalMaterial = MetalMaterial;
            if (!HasMetalFinish || metalMaterial == null)
            {
                ReleaseMetalAppearance();
                return;
            }

            var source = GetMeshRenderer();
            var skinned = source as SkinnedMeshRenderer;
            var filter = source != null ? source.GetComponent<MeshFilter>() : null;
            var mesh = skinned != null ? skinned.sharedMesh : filter != null ? filter.sharedMesh : null;
            if (source == null || mesh == null || mesh.subMeshCount == 0)
            {
                ReleaseMetalAppearance();
                return;
            }

            if (metalOverlayRenderer == null || metalSourceRenderer != source)
            {
                ReleaseMetalAppearance();
                metalSourceRenderer = source;
                metalOverlayObject = new GameObject("Metal Finish Overlay")
                {
                    hideFlags = HideFlags.HideAndDontSave,
                    layer = source.gameObject.layer
                };
                metalOverlayObject.transform.SetParent(source.transform, false);
                if (skinned != null)
                    metalOverlayRenderer = metalOverlayObject.AddComponent<SkinnedMeshRenderer>();
                else
                {
                    metalOverlayObject.AddComponent<MeshFilter>();
                    metalOverlayRenderer = metalOverlayObject.AddComponent<MeshRenderer>();
                }
                metalOverlayRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                metalOverlayRenderer.receiveShadows = source.receiveShadows;
            }

            metalOverlayRenderer.enabled = source.enabled;
            metalOverlayObject.layer = source.gameObject.layer;
            metalOverlayRenderer.renderingLayerMask = source.renderingLayerMask;
            metalOverlayRenderer.sortingLayerID = source.sortingLayerID;
            metalOverlayRenderer.sortingOrder = source.sortingOrder;
            metalOverlayRenderer.lightProbeUsage = source.lightProbeUsage;
            metalOverlayRenderer.reflectionProbeUsage = source.reflectionProbeUsage;
            metalOverlayRenderer.probeAnchor = source.probeAnchor;
            if (skinned != null)
            {
                var overlay = (SkinnedMeshRenderer)metalOverlayRenderer;
                if (overlay.sharedMesh != mesh)
                {
                    overlay.sharedMesh = mesh;
                    overlay.bones = skinned.bones;
                    overlay.rootBone = skinned.rootBone;
                }
                overlay.localBounds = skinned.localBounds;
                overlay.quality = skinned.quality;
                overlay.updateWhenOffscreen = skinned.updateWhenOffscreen;
                for (int i = 0; i < mesh.blendShapeCount; i++)
                    overlay.SetBlendShapeWeight(i, skinned.GetBlendShapeWeight(i));
            }
            else
                metalOverlayObject.GetComponent<MeshFilter>().sharedMesh = mesh;

            if (appliedMetalMaterial != metalMaterial || appliedMetalSubmeshCount != mesh.subMeshCount)
            {
                var materials = new Material[mesh.subMeshCount];
                for (int i = 0; i < materials.Length; i++)
                    materials[i] = metalMaterial;
                metalOverlayRenderer.sharedMaterials = materials;
                appliedMetalMaterial = metalMaterial;
                appliedMetalSubmeshCount = mesh.subMeshCount;
            }

            metalPropertyBlock ??= new MaterialPropertyBlock();
            metalPropertyBlock.Clear();
            metalPropertyBlock.SetColor(MetalTintId,
                metalFinish == MetalFinish.Gold ? new Color(1f, 1f, 0f, 1f) : Color.white);
            metalPropertyBlock.SetFloat(MetalBlendId, Mathf.Clamp01(metalBlend));
            metalPropertyBlock.SetFloat(RainbowStrengthId, HasRainbowFinish ? 1f : 0f);
            metalPropertyBlock.SetFloat(RainbowSpeedId, rainbowSpeed);
            metalPropertyBlock.SetFloat(RainbowScaleId, rainbowScale);
            metalPropertyBlock.SetFloat(RainbowRotationId, Mathf.Clamp(rainbowRotation, 0f, 360f));
            metalPropertyBlock.SetFloat(CosmicStrengthId, HasCosmicFinish ? 1f : 0f);
            metalPropertyBlock.SetFloat(CosmicBrightnessId, Mathf.Clamp(cosmicBrightness, 0f, 10f));
            metalPropertyBlock.SetFloat(CosmicScaleId, Mathf.Clamp(cosmicScale, 0.1f, 1f));
            metalPropertyBlock.SetFloat(CosmicSpeedId, Mathf.Clamp(cosmicSpeed, -2f, 2f));
            var cosmicTexture = CosmicCubemap;
            if (HasCosmicFinish && cosmicTexture != null)
                metalPropertyBlock.SetTexture(CosmicCubemapId, cosmicTexture);
            // Normalize in mesh space so moving/scaling the object does not slide the bands.
            var bounds = mesh.bounds;
            var center = bounds.center;
            var height = Mathf.Max(bounds.size.y, 0.0001f);
            metalPropertyBlock.SetVector(RainbowBoundsId,
                new Vector4(center.x, center.y, center.z, 1f / height));
            metalOverlayRenderer.SetPropertyBlock(metalPropertyBlock);
#if UNITY_EDITOR
            if (HasAnimatedMetalFinish && !Application.isPlaying)
            {
                if (!rainbowPreviewSubscribed)
                {
                    EditorApplication.update += UpdateRainbowEditorPreview;
                    rainbowPreviewSubscribed = true;
                }
            }
            else if (rainbowPreviewSubscribed)
                StopRainbowEditorPreview();
#endif
        }

        private void ReleaseMetalAppearance()
        {
#if UNITY_EDITOR
            StopRainbowEditorPreview();
#endif
            if (metalOverlayObject != null)
            {
                // Hide the old overlay immediately while runtime destruction is deferred.
                metalOverlayObject.SetActive(false);
                if (Application.isPlaying)
                    Destroy(metalOverlayObject);
                else
                    DestroyImmediate(metalOverlayObject);
            }
            metalOverlayObject = null;
            metalOverlayRenderer = null;
            metalSourceRenderer = null;
            appliedMetalMaterial = null;
            appliedMetalSubmeshCount = 0;
        }
    }
}
