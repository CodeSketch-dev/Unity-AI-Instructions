using System.Collections.Generic;
using Sirenix.OdinInspector;
using UnityEngine;

namespace Base_VanHuy
{
    [CreateAssetMenu(fileName = "TextureDataAsset", menuName = "Bounce Library/Texture Data Asset")]
    public class TextureDataAsset : ScriptableObject
    {
        private const string OpaqueMaterialReferenceName = "Opaque Material";
        private const string TransparentMaterialReferenceName = "Transparent Material";
        private const string MetalMaterialReferenceName = "Metal Material";
        private const string LegoDetailTextureReferenceName = "Lego Detail Texture 1";
        private const string LegoNormalTextureReferenceName = "Lego Normal Texture 1";
        private const string CheckerDetailTextureReferenceName = "Checker Detail Texture";
        private const string CosmicCubemapReferenceName = "Cube Map Cosmic";

        [System.Serializable]
        public class LegoTextureData
        {
            [SerializeField, AssetsOnly] private Texture2D legoDetail;
            [SerializeField, AssetsOnly] private Texture2D legoNormal;

            public Texture2D LegoDetail => legoDetail;
            public Texture2D LegoNormal => legoNormal;
        }

        [System.Serializable]
        private class DefaultAssetReference
        {
            [SerializeField] private string referenceName;
            [SerializeField, AssetsOnly] private Object asset;

            public bool Matches(string name) => referenceName == name;
            public T GetAsset<T>() where T : Object => asset as T;
        }

        [SerializeField] private List<Texture2D> albedoTextures = new List<Texture2D>();

        [FoldoutGroup("Lego Detail Textures")]
        [SerializeField] private List<LegoTextureData> legoTextures = new List<LegoTextureData>();

        [FoldoutGroup("Default Asset References")]
        [SerializeField] private List<DefaultAssetReference> defaultAssetReferences = new List<DefaultAssetReference>();

        public IReadOnlyList<Texture2D> AlbedoTextures => albedoTextures != null ? albedoTextures : System.Array.Empty<Texture2D>();
        public IReadOnlyList<LegoTextureData> LegoTextures => legoTextures != null ? legoTextures : System.Array.Empty<LegoTextureData>();
        public Material OpaqueMaterial => GetDefaultAsset<Material>(OpaqueMaterialReferenceName);
        public Material TransparentMaterial => GetDefaultAsset<Material>(TransparentMaterialReferenceName);
        public Material MetalMaterial => GetDefaultAsset<Material>(MetalMaterialReferenceName);
        public Cubemap CosmicCubemap => GetDefaultAsset<Cubemap>(CosmicCubemapReferenceName);
        public Texture2D LegoDetailTexture => GetDefaultAsset<Texture2D>(LegoDetailTextureReferenceName);
        public Texture2D LegoNormalTexture => GetDefaultAsset<Texture2D>(LegoNormalTextureReferenceName);
        public Texture2D CheckerDetailTexture => GetDefaultAsset<Texture2D>(CheckerDetailTextureReferenceName);

        private T GetDefaultAsset<T>(string referenceName) where T : Object
        {
            if (defaultAssetReferences == null)
                return null;

            foreach (var assetReference in defaultAssetReferences)
            {
                if (assetReference != null && assetReference.Matches(referenceName))
                    return assetReference.GetAsset<T>();
            }

            return null;
        }
    }
}
