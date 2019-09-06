using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class ButtonController : MonoBehaviour
{

    [SerializeField]
    private Text myText = null;
    private string actionURL = "";

    public void SetText(string buttonText, string buttonActionURL)
    {
        myText.text = buttonText;
        actionURL = buttonActionURL;
    }

    public void OnClick()
    {
        GameManager.LoseFocus();
        GameObject.Find("GameManager").GetComponent<GameManager>().DoAction(actionURL);
    }
}
