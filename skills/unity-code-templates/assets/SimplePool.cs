using System.Collections.Generic;
using UnityEngine;

namespace Game
{
    // Minimal prefab pool. Use the project's pool (PoolManager/LeanPool) when it exists; this is the fallback.
    public class SimplePool<T> where T : Component
    {
        readonly T _prefab;
        readonly Transform _root;
        readonly Stack<T> _free = new Stack<T>();

        public SimplePool(T prefab, Transform root, int prewarm = 0)
        {
            _prefab = prefab;
            _root = root;

            for (int i = 0; i < prewarm; i++)
            {
                T item = Object.Instantiate(_prefab, _root);
                item.gameObject.SetActive(false);
                _free.Push(item);
            }
        }

        public T Get(Vector3 position, Quaternion rotation)
        {
            T item = _free.Count > 0 ? _free.Pop() : Object.Instantiate(_prefab, _root);

            while (item == null)
            {
                item = _free.Count > 0 ? _free.Pop() : Object.Instantiate(_prefab, _root);
            }

            item.transform.SetPositionAndRotation(position, rotation);
            item.gameObject.SetActive(true);
            return item;
        }

        public void Release(T item)
        {
            if (item == null) return;

            item.gameObject.SetActive(false);
            item.transform.SetParent(_root, false);
            _free.Push(item);
        }
    }
}
