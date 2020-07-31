using Newtonsoft.Json.Linq;
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class SurveyManager : MonoBehaviour
{

    [SerializeField]
    private GameObject questionnairePanel;

    private GameObject message;
    private ArrayList buttonGroups;

#pragma warning disable CS0618 // Type or member is obsolete
    public WWW www = null;
#pragma warning restore CS0618 // Type or member is obsolete

    // Start is called before the first frame update
    void Start()
    {
        buttonGroups = new ArrayList();
        if (StaticVariables.survey)
        {
            StartCoroutine(Request(GameManager.SERVER + "reqsurvey"));
        }
        else
        {
            message = AddQuestion("");
            SendSurvey();
        }
    }

    IEnumerator Request(string url)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        using (www = new WWW(url))
#pragma warning restore CS0618 // Type or member is obsolete
        {
            yield return www;
            if (www.text.Length == 0)
            {
                yield break;
            }
            if (url.Contains("reqsurvey"))
            {
                JObject jo = JObject.Parse(www.text);
                int questionId = 0;
                for (int s = 0; s < jo.Count; s++)
                {
                    AddHeader(jo[s.ToString()]["description"].Value<string>());
                    ArrayList questions = jo[s.ToString()]["questions"].ToObject<ArrayList>();
                    foreach (JObject q in questions)
                    {
                        GameObject question = AddQuestion(q["question"].Value<string>());
                        ArrayList answers = q["answers"].ToObject<ArrayList>();
                        question.transform.name = "QuestionQ" + question;
                        int answerId = 0;
                        buttonGroups.Add(question);
                        foreach (string a in answers)
                        {
                            GameObject answer = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Survey/Answer"));
                            answer.transform.GetComponentInChildren<Text>().text = a;
                            answer.transform.SetParent(questionnairePanel.transform);
                            answer.GetComponent<Toggle>().group = question.GetComponent<ToggleGroup>();
                            answer.transform.name = "AnswerQ" + questionId + "=" + answerId;
                            answerId++;
                        }
                        questionId++;
                    }
                    AddHeader("");
                }
                AddButton("Send survey", SendSurvey);
                AddHeader("");
                message = AddQuestion("");
                for (int i = 0; i < 3; i++)
                {
                    AddHeader("");
                }
            }
            else
            {
                foreach (Transform child in questionnairePanel.transform)
                {
                    Destroy(child.gameObject);
                }
                AddHeader("Thank you for participating!");
                AddHeader("");
                AddQuestion("You may now close the window");
                AddHeader("");
                AddButton("Play again", PlayAgain);
            }
        }
    }

    public GameObject AddHeader(string text)
    {
        GameObject header = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Survey/Header"));
        header.GetComponent<Text>().text = text;
        header.transform.SetParent(questionnairePanel.transform);
        return header;
    }

    public GameObject AddQuestion(string text)
    {
        GameObject question = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Survey/Question"));
        question.GetComponent<Text>().text = text;
        question.transform.SetParent(questionnairePanel.transform);
        return question;
    }

    public GameObject AddButton(string text, UnityEngine.Events.UnityAction function)
    {
        GameObject button = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Survey/Button"));
        button.GetComponentInChildren<Text>().text = text;
        button.GetComponent<Button>().onClick.AddListener(function);
        button.transform.SetParent(questionnairePanel.transform);
        return button;
    }

    public void SendSurvey()
    {
        string query = "";
        if(buttonGroups.Count > 0)
        {
            foreach (GameObject question in buttonGroups)
            {
                foreach (Toggle toggle in question.GetComponent<ToggleGroup>().ActiveToggles())
                {
                    query += "&" + toggle.transform.name.Substring(6);
                }
            }
        }
        message.GetComponent<Text>().text = "Sending survey...";
        StartCoroutine(Request(GameManager.SERVER + "survey" + StaticVariables.gid + "?pid=" + StaticVariables.pid + query));
    }

    public void PlayAgain()
    {
        StaticVariables.gid = null;
        SceneManager.LoadScene("Scenes/GameScene", LoadSceneMode.Single);
    }
}
