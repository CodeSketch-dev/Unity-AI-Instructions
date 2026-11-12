using UnityEngine;
using UnityEngine.EventSystems;

namespace Game
{
    // Press feedback without any tween library: shrinks to PRESSED_SCALE while held, eases back on release.
    // Works for world-space buttons too (needs a Physics Raycaster on the camera + EventSystem).
    public class ButtonPressScale : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
    {
        const float PRESSED_SCALE = 0.93f;

        [SerializeField] float _speed = 18f;

        Vector3 _baseScale;
        float _target = 1f;
        float _current = 1f;

        void Awake()
        {
            _baseScale = transform.localScale;
        }

        void OnEnable()
        {
            _target = 1f;
            _current = 1f;
            transform.localScale = _baseScale;
        }

        void Update()
        {
            if (Mathf.Approximately(_current, _target)) return;

            _current = Mathf.MoveTowards(_current, _target, (1f - PRESSED_SCALE) * _speed * Time.unscaledDeltaTime);
            transform.localScale = _baseScale * _current;
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            _target = PRESSED_SCALE;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            _target = 1f;
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            _target = 1f;
        }
    }
}
