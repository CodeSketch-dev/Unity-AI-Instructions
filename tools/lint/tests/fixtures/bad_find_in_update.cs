using UnityEngine;

namespace Game
{
    public class Enemy_Chase : MonoBehaviour
    {
        void Update()
        {
            var player = Object.FindObjectOfType<Player>();
            if (player == null) return;
            transform.position = Vector3.MoveTowards(transform.position, player.transform.position, 3f * Time.deltaTime);
        }
    }
}
