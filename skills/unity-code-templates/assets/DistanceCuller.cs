using UnityEngine;

namespace Game
{
    // Event-driven distance culling for many small renderers (decor, props, world text).
    // No per-frame loop over objects: CullingGroup calls back only when an object crosses the distance band or visibility.
    public class DistanceCuller : MonoBehaviour
    {
        [SerializeField] Renderer[] _renderers;
        [SerializeField] float _showDistance = 80f;

        CullingGroup _group;

        void OnEnable()
        {
            Camera cam = Camera.main;
            if (cam == null || _renderers == null || _renderers.Length == 0) return;

            var spheres = new BoundingSphere[_renderers.Length];
            for (int i = 0; i < _renderers.Length; i++)
            {
                if (_renderers[i] == null) continue;
                Bounds b = _renderers[i].bounds;
                spheres[i] = new BoundingSphere(b.center, b.extents.magnitude);
            }

            _group = new CullingGroup { targetCamera = cam };
            _group.SetBoundingSpheres(spheres);
            _group.SetBoundingSphereCount(spheres.Length);
            _group.SetBoundingDistances(new[] { _showDistance });
            _group.SetDistanceReferencePoint(cam.transform);
            _group.onStateChanged = OnStateChanged;

            for (int i = 0; i < _renderers.Length; i++)
            {
                if (_renderers[i] != null)
                {
                    _renderers[i].enabled = _group.IsVisible(i) && _group.GetDistance(i) == 0;
                }
            }
        }

        void OnDisable()
        {
            if (_group == null) return;

            _group.onStateChanged = null;
            _group.Dispose();
            _group = null;
        }

        void OnStateChanged(CullingGroupEvent e)
        {
            Renderer r = _renderers[e.index];
            if (r != null)
            {
                r.enabled = e.isVisible && e.currentDistance == 0;
            }
        }
    }
}
