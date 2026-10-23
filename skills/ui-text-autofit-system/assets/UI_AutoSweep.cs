using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace Game
{
    // One-click, fully automatic UI/text pass over EVERY prefab under Assets/_Game: instantiates each prefab on a 1920x1080 reference canvas (so stretched rects have real sizes),
    // applies UI_TextAutoFit, rebuilds layouts, measures every text (textBounds vs rect) and writes what is still wrong to docs/ui-sweep-report.txt. Fixed prefabs are saved.
    // Menu: Tools/UI/Auto Sweep All Prefabs. Runs in small slices per editor tick so Unity stays responsive.
    public static class UI_AutoSweep
    {
        static readonly string[] SKIP = { "KnifeTowerReference", "/Tool", "Cheat", "Debug", "/Editor/" };
        const int PER_TICK = 6;

        static List<string> s_paths;
        static int s_i, s_changed, s_texts, s_issues, s_skipped;
        static StringBuilder s_report;
        static GameObject s_canvas;
        public static string Status = "idle";

        [MenuItem("Tools/UI/Auto Sweep All Prefabs")]
        public static void Start()
        {
            if (EditorApplication.isPlaying) { Status = "stop Play first"; return; }
            s_paths = AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/_Game" }).Select(AssetDatabase.GUIDToAssetPath)
                .Where(p => !SKIP.Any(p.Contains)).ToList();
            s_i = s_changed = s_texts = s_issues = s_skipped = 0;
            s_report = new StringBuilder();
            s_canvas = new GameObject("__UI_AutoSweep", typeof(RectTransform), typeof(Canvas));
            s_canvas.hideFlags = HideFlags.HideAndDontSave;
            s_canvas.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace;
            ((RectTransform)s_canvas.transform).sizeDelta = new Vector2(1920f, 1080f);
            Status = "running 0/" + s_paths.Count;
            EditorApplication.update += Tick;
        }

        static void Tick()
        {
            for (int n = 0; n < PER_TICK && s_i < s_paths.Count; n++)
            {
                try { Process(s_paths[s_i]); }
                catch (Exception e) { s_skipped++; s_report.AppendLine("SKIP " + s_paths[s_i] + ": " + e.Message); }
                s_i++;
            }
            Status = "running " + s_i + "/" + s_paths.Count;
            if (s_i < s_paths.Count) return;

            EditorApplication.update -= Tick;
            if (s_canvas != null) UnityEngine.Object.DestroyImmediate(s_canvas);
            AssetDatabase.SaveAssets();
            string head = "prefabs " + s_paths.Count + " texts " + s_texts + " prefabsChanged " + s_changed + " unresolvedIssues " + s_issues + " skipped " + s_skipped;
            string file = "D:/GitProject/thunder-break-egg/docs/ui-sweep-report.txt";
            File.WriteAllText(file, head + "\n" + s_report);
            Status = "done: " + head;
            Debug.Log("[UI_AutoSweep] " + head);
        }

        static void Process(string path)
        {
            var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (asset == null || asset.GetComponentInChildren<TMP_Text>(true) == null) return;
            bool ui = asset.GetComponent<RectTransform>() != null && !asset.GetComponentsInChildren<Canvas>(true).Any(c => c.renderMode == RenderMode.WorldSpace);

            var inst = (GameObject)PrefabUtility.InstantiatePrefab(asset, ui ? s_canvas.transform : null);
            try
            {
                if (ui)
                {
                    var rt = (RectTransform)inst.transform;
                    if (rt.anchorMin != rt.anchorMax)   // full-screen popups: give them the reference screen
                    { rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero; }
                    LayoutRebuilder.ForceRebuildLayoutImmediate(rt);
                }

                int changed = 0;
                foreach (TMP_Text t in inst.GetComponentsInChildren<TMP_Text>(true))
                    if (UI_TextAutoFit.Normalize(t, ui)) changed++;
                if (ui) LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)inst.transform);

                foreach (TMP_Text t in inst.GetComponentsInChildren<TMP_Text>(true))
                {
                    if (string.IsNullOrEmpty(t.text)) continue;
                    s_texts++;
                    RectTransform r = t.rectTransform;
                    if (r.rect.width < 1f || r.rect.height < 1f) continue;
                    t.ForceMeshUpdate();
                    float availW = r.rect.width - t.margin.x - t.margin.z;
                    Vector2 b = t.textBounds.size;
                    // TMP bounds overshoot the rect by a few px even when auto size fits; only text stuck at its minimum font is really too wide.
                    bool stuck = !t.enableAutoSizing || t.fontSize <= t.fontSizeMin + 0.1f;
                    if (stuck && b.x > availW * 1.03f + 2f && ui && r.anchorMin.x == r.anchorMax.x && r.parent is RectTransform pr)
                    {   // still too wide at the smallest font: widen the text's own rect (centred) up to the parent's width minus padding
                        float need = b.x + t.margin.x + t.margin.z + 4f;
                        float widened = Mathf.Min(need, pr.rect.width - 16f);
                        if (widened > r.rect.width) { r.sizeDelta = new Vector2(r.sizeDelta.x + (widened - r.rect.width), r.sizeDelta.y); changed++; t.ForceMeshUpdate(); b = t.textBounds.size; availW = r.rect.width - t.margin.x - t.margin.z; }
                    }
                    if (stuck && b.x > availW * 1.03f + 2f && ui)
                    {   // last resorts, in order: slimmer side padding, then a smaller minimum font (never overflow beats the 18 floor)
                        t.margin = new Vector4(Mathf.Min(t.margin.x, 3f), t.margin.y, Mathf.Min(t.margin.z, 3f), t.margin.w);
                        t.ForceMeshUpdate(); changed++;
                        for (float min = t.fontSizeMin; min > 14f; )
                        {
                            availW = r.rect.width - t.margin.x - t.margin.z; b = t.textBounds.size;
                            if (b.x <= availW * 1.03f + 2f) break;
                            min -= 1f; t.fontSizeMin = min; t.ForceMeshUpdate();
                        }
                        availW = r.rect.width - t.margin.x - t.margin.z; b = t.textBounds.size;
                    }
                    if (b.x > availW * 1.03f + 2f || b.y > r.rect.height * 1.03f + 2f)
                    {
                        s_issues++;
                        s_report.AppendLine("OVERFLOW " + path + " / " + Hierarchy(t.transform, inst.transform) + " '" + Trim(t.text) + "' bounds " + (int)b.x + "x" + (int)b.y + " avail " + (int)availW + "x" + (int)r.rect.height);
                    }
                }

                if (changed > 0)
                {
                    PrefabUtility.ApplyPrefabInstance(inst, InteractionMode.AutomatedAction);
                    s_changed++;
                }
            }
            finally { UnityEngine.Object.DestroyImmediate(inst); }
        }

        static string Hierarchy(Transform t, Transform root)
        {
            var parts = new List<string>();
            for (; t != null && t != root; t = t.parent) parts.Add(t.name);
            parts.Reverse();
            return string.Join("/", parts);
        }

        static string Trim(string s) => s.Length > 40 ? s.Substring(0, 40) : s;
    }
}
