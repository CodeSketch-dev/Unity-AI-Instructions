using Sirenix.OdinInspector;
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Base_VanHuy
{
    public partial class TextureTypeComponent
    {
#if UNITY_EDITOR
        private const string ShaderLibraryPath = "Assets/_Game/RobloxShaderKit/Runtime/Data";
        private const string DefaultTextureDataAssetPath = ShaderLibraryPath + "/Textures/TextureDataAsset.asset";
        private const int AlbedoTexturesPerPage = 5;
        private const float AlbedoTextureCellSize = 32f;

        private int albedoTexturePage;
        private int legoDetailTexturePage;
        private bool isMaterialPreviewUpdateQueued;
        private System.Collections.Generic.Dictionary<Renderer, MaterialPropertyBlock> colorPreviewPropertyBlocks;

        [FoldoutGroup("Solid Color"), OnInspectorGUI]
        private void DrawSolidColorGroup()
        {
            EditorGUI.BeginChangeCheck();
            var updatedSolidColor = EditorGUILayout.ColorField("Color", solidColor);
            if (!EditorGUI.EndChangeCheck()) return;

            foreach (var target in GetInspectorTargets())
            {
                Undo.RecordObject(target, "Change Solid Color");
                target.solidColor = updatedSolidColor;
                target.PreviewInspectorColor();
                EditorUtility.SetDirty(target);
            }
        }

        private void PreviewInspectorColor()
        {
            if (!isActiveAndEnabled)
                return;

            if (colorPreviewPropertyBlocks == null)
            {
                colorPreviewPropertyBlocks = new System.Collections.Generic.Dictionary<Renderer, MaterialPropertyBlock>();
                EditorApplication.update += CommitInspectorColorPreviewWhenReady;
                Selection.selectionChanged += CommitInspectorColorPreview;
            }

            var previewColor = solidColor;
            previewColor.a = isTransparent ? previewColor.a : 1f;
            foreach (var targetRenderer in GetComponents<Renderer>())
            {
                if (!colorPreviewPropertyBlocks.ContainsKey(targetRenderer))
                {
                    var originalBlock = new MaterialPropertyBlock();
                    targetRenderer.GetPropertyBlock(originalBlock);
                    colorPreviewPropertyBlocks.Add(targetRenderer, originalBlock);
                }

                var previewBlock = new MaterialPropertyBlock();
                targetRenderer.GetPropertyBlock(previewBlock);
                previewBlock.SetColor("_BaseColor", previewColor);
                previewBlock.SetColor("_Color", previewColor);
                targetRenderer.SetPropertyBlock(previewBlock);
            }
        }

        private void CommitInspectorColorPreviewWhenReady()
        {
            if (this == null)
            {
                EditorApplication.update -= CommitInspectorColorPreviewWhenReady;
                Selection.selectionChanged -= CommitInspectorColorPreview;
                return;
            }

            if (EditorGUIUtility.editingTextField || IsColorPickerOpen())
                return;

            CommitInspectorColorPreview();
        }

        private static bool IsColorPickerOpen()
        {
            foreach (var window in Resources.FindObjectsOfTypeAll<EditorWindow>())
            {
                if (window.GetType().FullName == "UnityEditor.ColorPicker")
                    return true;
            }

            return false;
        }

        private void CommitInspectorColorPreview()
        {
            if (colorPreviewPropertyBlocks == null)
                return;

            ClearInspectorColorPreview();
            if (this == null || !isActiveAndEnabled)
                return;

            if (Application.isPlaying)
                CreateAndAssignMaterialClones();
            else
                UpdateMaterialPreview();
        }

        private void ClearInspectorColorPreview()
        {
            if (colorPreviewPropertyBlocks == null)
                return;

            EditorApplication.update -= CommitInspectorColorPreviewWhenReady;
            Selection.selectionChanged -= CommitInspectorColorPreview;
            foreach (var entry in colorPreviewPropertyBlocks)
            {
                if (entry.Key != null)
                    entry.Key.SetPropertyBlock(entry.Value);
            }

            colorPreviewPropertyBlocks = null;
        }

        [FoldoutGroup("Solid Color"), OnInspectorGUI]
        private void DrawTransparency()
        {
            EditorGUI.BeginChangeCheck();
            var updatedIsTransparent = EditorGUILayout.Toggle("Is Transparent", isTransparent);
            if (!EditorGUI.EndChangeCheck()) return;

            foreach (var target in GetInspectorTargets())
            {
                Undo.RecordObject(target, "Change Transparency");
                target.isTransparent = updatedIsTransparent;
                target.ApplyInspectorMaterialChanges();
                EditorUtility.SetDirty(target);
            }
        }

        [FoldoutGroup("Texture Data"), OnInspectorGUI]
        private void DrawTextureDataGroup()
        {
            EditorGUI.BeginChangeCheck();
            var updatedApplyTextureData = EditorGUILayout.Toggle("Apply", applyTextureData);
            var updatedAlbedoTexture = albedoTexture;
            var updatedLegoDetailTexture = legoDetailTexture;
            var updatedLegoNormalTexture = legoNormalTexture;
            var updatedIsAlbedoMovement = isAlbedoMovement;
            var updatedIsLegoDetail = isLegoDetail;
            var updatedIsCheckerDetail = isCheckerDetail;
            if (updatedApplyTextureData)
            {
                updatedAlbedoTexture = DrawAlbedoTextureGrid(textureDataAsset, albedoTexture);
                updatedIsAlbedoMovement = EditorGUILayout.Toggle("Is Albedo Movement", isAlbedoMovement);
                updatedIsLegoDetail = EditorGUILayout.Toggle("Is LegoDetail", isLegoDetail);
                if (updatedIsLegoDetail)
                    updatedLegoDetailTexture = DrawLegoTextureGrid(textureDataAsset, legoDetailTexture, legoNormalTexture,
                        out updatedLegoNormalTexture);
                updatedIsCheckerDetail = EditorGUILayout.Toggle("Is CheckerDetail", isCheckerDetail);
            }

            if (!EditorGUI.EndChangeCheck()) return;

            foreach (var target in GetInspectorTargets())
            {
                Undo.RecordObject(target, "Change Texture Data");
                target.applyTextureData = updatedApplyTextureData;
                target.albedoTexture = updatedAlbedoTexture;
                target.legoDetailTexture = updatedLegoDetailTexture;
                target.legoNormalTexture = updatedLegoNormalTexture;
                target.isAlbedoMovement = updatedIsAlbedoMovement;
                target.isLegoDetail = updatedIsLegoDetail;
                target.isCheckerDetail = updatedIsCheckerDetail;
                target.ApplyInspectorMaterialChanges();
                EditorUtility.SetDirty(target);
            }
        }

        [FoldoutGroup("Advanced Options"), OnInspectorGUI]
        private void DrawAdvancedOptionsGroup()
        {
            EditorGUI.BeginChangeCheck();
            var updatedCheckerTiling = EditorGUILayout.FloatField("Checker Tiling", checkerTiling);
            var updatedLegoTiling = EditorGUILayout.FloatField("Lego Tiling", legoTiling);
            var updatedMovementXY = EditorGUILayout.Vector2Field("Movement X/Y", movementXY);
            var updatedEnableEmission = EditorGUILayout.Toggle("Emission", enableEmission);
            var updatedEmissionStrength = updatedEnableEmission
                ? EditorGUILayout.Slider("Emission Strength", emissionStrength, 0f, 10f)
                : emissionStrength;
            if (!EditorGUI.EndChangeCheck()) return;

            foreach (var target in GetInspectorTargets())
            {
                Undo.RecordObject(target, "Change Advanced Options");
                target.checkerTiling = Mathf.Max(0f, updatedCheckerTiling);
                target.legoTiling = Mathf.Max(0f, updatedLegoTiling);
                target.movementXY = updatedMovementXY;
                target.enableEmission = updatedEnableEmission;
                target.emissionStrength = Mathf.Clamp(updatedEmissionStrength, 1f, 10f);
                target.ApplyInspectorMaterialChanges();
                EditorUtility.SetDirty(target);
            }
        }

        private Texture2D DrawAlbedoTextureGrid(TextureDataAsset dataAsset, Texture2D selectedTexture)
        {
            if (dataAsset == null)
            {
                EditorGUILayout.HelpBox("Assign a Texture Data Asset to select an Albedo texture.", MessageType.Info);
                return null;
            }

            var textures = dataAsset.AlbedoTextures;
            var textureCount = textures.Count + 1;
            var pageCount = Mathf.Max(1, Mathf.CeilToInt(textureCount / (float)AlbedoTexturesPerPage));
            albedoTexturePage = Mathf.Clamp(albedoTexturePage, 0, pageCount - 1);
            var updatedTexture = selectedTexture;

            EditorGUILayout.BeginHorizontal();
            var albedoLabelStyle = new GUIStyle(EditorStyles.label) { alignment = TextAnchor.MiddleLeft };
            GUILayout.Label("Albedo", albedoLabelStyle, GUILayout.Width(EditorGUIUtility.labelWidth), GUILayout.Height(AlbedoTextureCellSize));
            EditorGUI.BeginDisabledGroup(albedoTexturePage == 0);
            if (GUILayout.Button("<", GUILayout.Width(20f), GUILayout.Height(AlbedoTextureCellSize))) albedoTexturePage--;
            EditorGUI.EndDisabledGroup();

            var firstTextureIndex = albedoTexturePage * AlbedoTexturesPerPage;
            var lastTextureIndex = Mathf.Min(firstTextureIndex + AlbedoTexturesPerPage, textureCount);
            for (var textureIndex = firstTextureIndex; textureIndex < lastTextureIndex; textureIndex++)
            {
                var texture = textureIndex == 0 ? null : textures[textureIndex - 1];
                if (DrawAlbedoTextureGridCell(texture, texture == selectedTexture)) updatedTexture = texture;
            }

            EditorGUI.BeginDisabledGroup(albedoTexturePage == pageCount - 1);
            if (GUILayout.Button(">", GUILayout.Width(20f), GUILayout.Height(AlbedoTextureCellSize))) albedoTexturePage++;
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.EndHorizontal();
            return updatedTexture;
        }

        private static bool DrawAlbedoTextureGridCell(Texture2D texture, bool isSelected)
        {
            var cellRect = GUILayoutUtility.GetRect(AlbedoTextureCellSize, AlbedoTextureCellSize, GUILayout.Width(AlbedoTextureCellSize), GUILayout.Height(AlbedoTextureCellSize));
            var backgroundColor = GUI.backgroundColor;
            if (isSelected) GUI.backgroundColor = Color.green;
            var wasSelected = GUI.Button(cellRect, GUIContent.none);
            GUI.backgroundColor = backgroundColor;
            if (texture != null)
                EditorGUI.DrawPreviewTexture(new Rect(cellRect.x + 2f, cellRect.y + 2f, cellRect.width - 4f, cellRect.height - 4f), texture, null, ScaleMode.ScaleToFit);
            else
                GUI.Label(cellRect, "None", EditorStyles.centeredGreyMiniLabel);
            return wasSelected;
        }

        private Texture2D DrawLegoTextureGrid(TextureDataAsset dataAsset, Texture2D selectedDetailTexture,
            Texture2D selectedNormalTexture, out Texture2D updatedNormalTexture)
        {
            updatedNormalTexture = selectedNormalTexture;
            if (dataAsset == null)
            {
                EditorGUILayout.HelpBox("Assign a Texture Data Asset to select a Lego Detail texture.", MessageType.Info);
                return null;
            }

            var legoTextures = dataAsset.LegoTextures;
            var textureCount = legoTextures.Count;
            var pageCount = Mathf.Max(1, Mathf.CeilToInt(textureCount / (float)AlbedoTexturesPerPage));
            legoDetailTexturePage = Mathf.Clamp(legoDetailTexturePage, 0, pageCount - 1);
            var updatedDetailTexture = selectedDetailTexture;

            EditorGUILayout.BeginHorizontal();
            var labelStyle = new GUIStyle(EditorStyles.label) { alignment = TextAnchor.MiddleLeft };
            GUILayout.Label("Lego Detail", labelStyle, GUILayout.Width(EditorGUIUtility.labelWidth), GUILayout.Height(AlbedoTextureCellSize));
            EditorGUI.BeginDisabledGroup(legoDetailTexturePage == 0);
            if (GUILayout.Button("<", GUILayout.Width(20f), GUILayout.Height(AlbedoTextureCellSize))) legoDetailTexturePage--;
            EditorGUI.EndDisabledGroup();

            var firstTextureIndex = legoDetailTexturePage * AlbedoTexturesPerPage;
            var lastTextureIndex = Mathf.Min(firstTextureIndex + AlbedoTexturesPerPage, textureCount);
            for (var textureIndex = firstTextureIndex; textureIndex < lastTextureIndex; textureIndex++)
            {
                var legoTexture = legoTextures[textureIndex];
                if (legoTexture == null || legoTexture.LegoDetail == null)
                    continue;

                var isSelected = legoTexture.LegoDetail == selectedDetailTexture && legoTexture.LegoNormal == selectedNormalTexture;
                if (!DrawAlbedoTextureGridCell(legoTexture.LegoDetail, isSelected))
                    continue;

                updatedDetailTexture = legoTexture.LegoDetail;
                updatedNormalTexture = legoTexture.LegoNormal;
            }

            EditorGUI.BeginDisabledGroup(legoDetailTexturePage == pageCount - 1);
            if (GUILayout.Button(">", GUILayout.Width(20f), GUILayout.Height(AlbedoTextureCellSize))) legoDetailTexturePage++;
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.EndHorizontal();
            return updatedDetailTexture;
        }

        private void QueueMaterialPreviewUpdate()
        {
            if (isMaterialPreviewUpdateQueued) return;
            isMaterialPreviewUpdateQueued = true;
            EditorApplication.delayCall += ApplyQueuedMaterialPreviewUpdate;
        }

        private void ApplyQueuedMaterialPreviewUpdate()
        {
            isMaterialPreviewUpdateQueued = false;
            if (this != null) UpdateMaterialPreview();
        }

        private void ApplyInspectorMaterialChanges()
        {
            if (Application.isPlaying) RefreshMaterialsIfPlaying();
            else QueueMaterialPreviewUpdate();
        }

        private TextureTypeComponent[] GetInspectorTargets()
        {
            var targets = new System.Collections.Generic.List<TextureTypeComponent>();
            foreach (var selectedGameObject in Selection.gameObjects)
            {
                var target = selectedGameObject.GetComponent<TextureTypeComponent>();
                if (target != null && !targets.Contains(target))
                    targets.Add(target);
            }

            if (targets.Count == 0)
                targets.Add(this);

            return targets.ToArray();
        }

        private void MarkEditorDirty()
        {
            EditorUtility.SetDirty(this);
        }

        private void RevertMaterialPrefabOverrides()
        {
            if (Application.isPlaying) return;
            foreach (var targetRenderer in GetComponents<Renderer>())
            {
                if (!PrefabUtility.IsPartOfPrefabInstance(targetRenderer)) continue;
                var serializedRenderer = new SerializedObject(targetRenderer);
                serializedRenderer.Update();
                var materialProperty = serializedRenderer.FindProperty("m_Materials");
                if (materialProperty == null || !materialProperty.prefabOverride) continue;
                PrefabUtility.RevertPropertyOverride(materialProperty, InteractionMode.AutomatedAction);
            }
        }

        private bool AssignDefaultTextureDataAssetIfNeeded()
        {
            if (textureDataAsset != null) return false;
            textureDataAsset = AssetDatabase.LoadAssetAtPath<TextureDataAsset>(DefaultTextureDataAssetPath);
            if (textureDataAsset != null) return true;
            var assetGuids = AssetDatabase.FindAssets("t:TextureDataAsset");
            if (assetGuids.Length > 0)
                textureDataAsset = AssetDatabase.LoadAssetAtPath<TextureDataAsset>(AssetDatabase.GUIDToAssetPath(assetGuids[0]));
            return textureDataAsset != null;
        }

        private bool AssignDefaultLegoTexturesIfNeeded()
        {
            if (textureDataAsset == null)
                return false;

            var wasAssigned = false;
            if (legoDetailTexture == null)
            {
                legoDetailTexture = textureDataAsset.LegoDetailTexture;
                wasAssigned = legoDetailTexture != null;
            }

            if (legoNormalTexture == null)
            {
                legoNormalTexture = textureDataAsset.LegoNormalTexture;
                wasAssigned |= legoNormalTexture != null;
            }

            return wasAssigned;
        }

#endif
    }
}
