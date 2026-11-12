using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game
{
    // Development-only cheat panel (IMGUI, zero art needed). Features register actions from their own code:
    //   DebugCheats.Register("Economy", "+1M money", () => Data_Wallet.Add(1_000_000));
    // Open with the backtick key (editor/PC) or a 3-finger tap (device). Compiled out of release builds.
    public class DebugCheats : MonoBehaviour
    {
#if DEVELOPMENT_BUILD || UNITY_EDITOR
        static readonly Dictionary<string, List<(string label, Action action)>> GROUPS = new Dictionary<string, List<(string, Action)>>();

        bool _open;
        Vector2 _scroll;
        string _group = "";
        float _timeScale = 1f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics()
        {
            GROUPS.Clear();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Bootstrap()
        {
            if (FindFirstObjectByType<DebugCheats>() != null) return;

            var go = new GameObject("DebugCheats");
            DontDestroyOnLoad(go);
            go.AddComponent<DebugCheats>();
        }

        public static void Register(string group, string label, Action action)
        {
            if (!GROUPS.TryGetValue(group, out var list))
            {
                list = new List<(string, Action)>();
                GROUPS[group] = list;
            }

            list.Add((label, action));
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.BackQuote) || (Input.touchCount == 3 && Input.GetTouch(2).phase == TouchPhase.Began))
            {
                _open = !_open;
            }
        }

        void OnGUI()
        {
            if (!_open) return;

            float w = Mathf.Min(Screen.width * 0.9f, 900f);
            GUILayout.BeginArea(new Rect((Screen.width - w) * 0.5f, 20, w, Screen.height - 40), GUI.skin.box);
            GUILayout.Label($"DEBUG  timeScale {Time.timeScale:0.#}");
            _timeScale = GUILayout.HorizontalSlider(_timeScale, 0f, 60f);
            if (!Mathf.Approximately(_timeScale, Time.timeScale)) Time.timeScale = _timeScale;
            if (GUILayout.Button("timeScale = 1")) { _timeScale = 1f; Time.timeScale = 1f; }

            GUILayout.BeginHorizontal();
            foreach (var key in GROUPS.Keys)
            {
                if (GUILayout.Button(key)) _group = key;
            }
            GUILayout.EndHorizontal();

            _scroll = GUILayout.BeginScrollView(_scroll);
            if (GROUPS.TryGetValue(_group, out var actions))
            {
                foreach (var (label, action) in actions)
                {
                    if (GUILayout.Button(label, GUILayout.Height(Screen.height * 0.05f)))
                    {
                        try { action(); }
                        catch (Exception e) { Debug.LogException(e); }
                    }
                }
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }
#endif
    }
}
