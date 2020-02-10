using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class BackgroundController : MonoBehaviour
{
    private bool showInformation;

    // Start is called before the first frame update
    void Start()
    {
        ModifyVisibility(true);
        showInformation = false;
    }

    // Update is called once per frame
    void Update()
    {
        if(Input.GetKey(KeyCode.Escape))
        {
            ModifyVisibility(true);
            showInformation = false;
        }
        if (Input.GetKey(KeyCode.Return))
        {
            ModifyVisibility(false);
        }
        if(Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl))
        {
            if (!showInformation)
            {
                ModifyVisibility(true);
            }
            
        }
        else
        {
            if (showInformation)
            {
                ModifyVisibility(false);
            }
        }
    }

    void ModifyVisibility(bool visibility)
    {
        showInformation = visibility;
        GetComponent<Image>().enabled = visibility;
        GameObject.Find("InfectionDeckDiscard").GetComponent<Text>().enabled = visibility;
        GameObject.Find("InfectionDeckPiles").GetComponent<Text>().enabled = visibility;
        GameObject.Find("PlayerDeckDiscard").GetComponent<Text>().enabled = visibility;
        GameObject.Find("GameControls").GetComponent<Text>().enabled = visibility;
        GameObject.Find("ToggleSkipAction").transform.localScale = visibility ? new Vector3(1, 1, 1) : new Vector3(0, 0, 0);
        GameObject.Find("GameLog").transform.localScale = visibility? new Vector3(1, 1, 1):new Vector3(0, 0, 0);
        GameManager.LoseFocus();
    }

}
