using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class AscendingAnimationScript : MonoBehaviour
{
    private static readonly float ascend = 1f;

    private Vector3 position;
    private float tStart,duration;
    private bool started;

    // Update is called once per frame
    void Update()
    {
        if (started)
        {
            float ttime = (Time.time - tStart) / duration;
            transform.position = position + Vector3.up * ascend * ttime;
            if (ttime >= 1.0f)
            {
                Destroy(gameObject);
            }
        }
    }

    public void BeginAnimation(GameObject parent,float duration)
    {
        position = parent.transform.position;
        transform.position = position;
        transform.SetParent(parent.transform);
        this.duration = duration;
        tStart = Time.time;
        started = true;
    }

}
