using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class ButtonController : MonoBehaviour
{
    [SerializeField]
    private Text myText;
    private string myURL;
    private bool endgame = false,accepted;

    public void SetText(string action, string actionURL)
    {
        myText.text = action;
        myURL = actionURL;
    }

    public void SetEndgame(bool acceptValue)
    {
        myText.text = acceptValue?"Yes":"Skip survey";
        accepted = acceptValue;
        endgame = true;
    }

    public void OnClick()
    {
        if (endgame)
        {
            StaticVariables.survey = accepted;
            SceneManager.LoadScene("Scenes/SurveyScene", LoadSceneMode.Single);
        }
        else
        {
            GameObject.Find("GameManager").GetComponent<GameManager>().DoAction(myURL);
        }
    }
}
