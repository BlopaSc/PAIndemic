using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EnlargeVanishAnimationScript : MonoBehaviour
{
    private Vector3 position;
    private float tStart, duration, initSize;
    private bool started;

    // Update is called once per frame
    void Update()
    {
        if (started)
        {
            float ttime = (Time.time - tStart) / duration;
            float size = initSize + 3.5f * Mathf.Clamp01(ttime + 0.25f);
            transform.localScale = new Vector3(size, size, 1.0f);
            GetComponent<SpriteRenderer>().color = new Color(1, 1, 1, Mathf.Clamp01((1.0f - ttime) * 1.25f));
            if (ttime >= 1.0f)
            {
                Destroy(gameObject);
            }
        }
    }

    public void BeginAnimation(GameObject parent, float duration, float initialSize=1.5f)
    {
        position = parent.transform.position;
        transform.position = position;
        transform.SetParent(parent.transform);
        this.duration = duration;
        initSize = initialSize;
        tStart = Time.time;
        started = true;
    }

}
