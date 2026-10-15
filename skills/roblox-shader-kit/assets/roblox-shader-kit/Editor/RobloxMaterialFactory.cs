using System;
using UnityEditor;
using UnityEngine;

namespace RobloxShaderKit.Editor
{
    public static class RobloxMaterialFactory
    {
        public const string Root = "Assets/_Game/RobloxShaderKit";
        public static Material Ensure()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Stop Play Mode first");
            var shader = AssetDatabase.LoadAssetAtPath<Shader>(Root + "/Runtime/Shaders/Roblox_Batched.shader");
            if (shader == null || !shader.isSupported || ShaderUtil.ShaderHasError(shader))
                throw new InvalidOperationException("Roblox shader missing or unsupported; fallback forbidden");
            string path = Root + "/M_RobloxWorld.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null) { material = new Material(shader); AssetDatabase.CreateAsset(material,path); }
            material.shader = shader;
            string[] properties = { "_Albedo1", "_Albedo2", "_Albedo3", "_CheckerDetail", "_LegoDetail", "_LegoNormal" };
            string[] textures = { "T_Water.png", "T_Lava.png", "T_Sand.png", "T@_Checker.png", "T@_Brick_Albedo.png", "T@_Brick_Normal.png" };
            for (int i = 0; i < properties.Length; i++)
            {
                var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/SourceContract/Textures/" + textures[i]);
                if (texture == null) throw new InvalidOperationException("Missing texture " + textures[i]);
                material.SetTexture(properties[i],texture);
            }
            material.SetColor("_BaseColor",Color.white); material.SetFloat("_Smoothness",0);
            material.SetFloat("_Metallic",0); material.SetFloat("_Cull",2);
            material.SetFloat("_ZWrite",1); material.renderQueue = 2000;
            material.EnableKeyword("_NORMALMAP");
            EditorUtility.SetDirty(material); AssetDatabase.SaveAssets(); return material;
        }
    }
}
