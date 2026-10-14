using UnityEngine;

namespace Game
{
    // Development-only FPS / memory readout. Add to any object in the boot scene; it removes itself from release builds.
    public class FpsOverlay : MonoBehaviour
    {
        [SerializeField] float _refreshSeconds = 0.5f;

#if DEVELOPMENT_BUILD || UNITY_EDITOR
        float _accumulated;
        int _frames;
        float _fps;
        float _worstFrameMs;
        GUIStyle _style;

        void Update()
        {
            _accumulated += Time.unscaledDeltaTime;
            _frames++;
            _worstFrameMs = Mathf.Max(_worstFrameMs, Time.unscaledDeltaTime * 1000f);

            if (_accumulated >= _refreshSeconds)
            {
                _fps = _frames / _accumulated;
                _accumulated = 0f;
                _frames = 0;
            }
        }

        void OnGUI()
        {
            _style ??= new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt(Screen.height * 0.025f) };
            float mb = (UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong() / 1048576f);
            GUI.Label(new Rect(10, 10, Screen.width, Screen.height * 0.05f), $"{_fps:0} fps  worst {_worstFrameMs:0}ms  mem {mb:0}MB", _style);
        }
#else
        void Awake()
        {
            Destroy(this);
        }
#endif
    }
}
