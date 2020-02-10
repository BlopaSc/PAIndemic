using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class MessageAnimator : MonoBehaviour
{
    public static float visible = 3.0f;
    private static Vector3 startingPos = new Vector3(-400f, -100f, 0f);
    private static Vector3 offset = new Vector3(0f,-50f,0f);
    private float time;
    private bool boost = false;
    public int msgnum = -1;
    // Start is called before the first frame update
    void Start()
    {
        time = 0f;
    }
    // Update is called once per frame
    void Update()
    {
        if(msgnum != -1)
        {
            GetComponent<RectTransform>().localPosition = startingPos + (float)(msgnum) * offset;
        }
        time += Time.deltaTime;
        Color myColor = GetComponent<Text>().color;
        if(myColor.a == 0)
        {
            Destroy(gameObject);
        }
        if (boost)
        {
            myColor.a = Mathf.Lerp(1f, 0f, time/(2*visible));
            GetComponent<Text>().color = myColor;
        }
        else
        {
            boost = visible >= time;
        }
 
    }
}
