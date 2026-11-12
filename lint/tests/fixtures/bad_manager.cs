using UnityEngine;

namespace Game
{
    public class Bootstrap : MonoBehaviour
    {
        void Awake()
        {
            var go = new GameObject("AudioManager");
            go.AddComponent<AudioManager>();
            DontDestroyOnLoad(go);
        }
    }
}
