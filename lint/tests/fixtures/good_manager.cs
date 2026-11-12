using UnityEngine;

namespace Game
{
    // The manager is a scene-authored prefab; code only reads it.
    public class Bootstrap : MonoBehaviour
    {
        [SerializeField] AudioManager _audio;

        void Awake() => _audio.Init();
    }
}
