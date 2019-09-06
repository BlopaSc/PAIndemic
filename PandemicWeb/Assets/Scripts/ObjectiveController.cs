using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class ObjectiveController : MonoBehaviour
{

    [SerializeField]
    private Sprite diseaseImage = null;
    [SerializeField]
    private Sprite cureImage = null;
    [SerializeField]
    private Sprite eradicatedImage = null;

    private int state = 0;

    // Start is called before the first frame update
    void Start()
    {
        GetComponent<Image>().sprite = diseaseImage;
    }

    public void UpdateState(bool cured,bool eradicated)
    {
        if(cured && state == 0)
        {
            state++;
            GetComponent<Image>().sprite = cureImage;
        }
        if(eradicated && state == 1)
        {
            state++;
            GetComponent<Image>().sprite = eradicatedImage;
        }
    }

}
