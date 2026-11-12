using UnityEngine;

namespace Game
{
    public class Enemy_Chase : MonoBehaviour
    {
        [SerializeField] Transform _target;

        void Update()
        {
            if (_target == null) return;
            transform.position = Vector3.MoveTowards(transform.position, _target.position, 3f * Time.deltaTime);
        }
    }
}
