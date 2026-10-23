using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game
{
    // Editor side of UI_TextAutoFit: every prefab / scene save normalises its texts, so authored UI is already correct (no runtime surprise, no manual pass).
    // Menu Tools/UI/Normalize Open Scene Texts does it on demand.
    [InitializeOnLoad]
    static class UI_TextAutoFit_Editor
    {
        static UI_TextAutoFit_Editor()
        {
            PrefabStage.prefabSaving += root => Run(root);
            EditorSceneManager.sceneSaving += (scene, path) =>
            {
                foreach (GameObject r in scene.GetRootGameObjects()) Run(r);
            };
        }

        static int Run(GameObject root)
        {
            int n = 0;
            foreach (TMP_Text t in root.GetComponentsInChildren<TMP_Text>(true))
                if (UI_TextAutoFit.Normalize(t)) { EditorUtility.SetDirty(t); n++; }
            return n;
        }

        [MenuItem("Tools/UI/Normalize Open Scene Texts")]
        static void NormalizeScene()
        {
            int n = 0;
            foreach (GameObject r in EditorSceneManager.GetActiveScene().GetRootGameObjects()) n += Run(r);
            Debug.Log("[UI_TextAutoFit] normalised " + n + " texts");
        }
    }
}
