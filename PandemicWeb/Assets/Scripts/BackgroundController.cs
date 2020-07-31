using UnityEngine;
using UnityEngine.UI;

public class BackgroundController : MonoBehaviour
{
    private GameObject gameLog;
    private GameObject skipMenu;
    private bool previous_visibility;
    // Start is called before the first frame update
    void Start()
    {
        gameLog = GameObject.Find("GameLog");
        skipMenu = GameObject.Find("SkipMenuToggle");
        SetVisibility(false);
    }

    // Update is called once per frame
    void Update()
    {
        bool visibility = (Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl));
        if (visibility != previous_visibility)
        {
            SetVisibility(visibility);
        }
    }

    void SetVisibility(bool visibility)
    {
        previous_visibility = visibility;
        GetComponent<Image>().enabled = visibility;
        GameObject.Find("InfectionDiscardText").GetComponent<Text>().enabled = visibility;
        GameObject.Find("PlayerDiscardText").GetComponent<Text>().enabled = visibility;
        gameLog.SetActive(visibility);
        skipMenu.SetActive(visibility);
    }
}
