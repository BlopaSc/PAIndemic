using Newtonsoft.Json.Linq;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class GameManager : MonoBehaviour
{
    public static readonly string[] colors = { "yellow", "red", "blue", "black" };
    public static readonly float eventTime = 0.5f;

    // LOCALHOST
    public const string SERVER = "http://127.0.0.1:31337/";
    // CUSTOM SERVER
    // public const string SERVER = "http://35.239.38.12:80/";

#pragma warning disable CS0618 // Type or member is obsolete
    public WWW www = null;
#pragma warning restore CS0618 // Type or member is obsolete

    [SerializeField]
    private GameObject waitingText;
    [SerializeField]
    private GameObject gameLog;
    [SerializeField]
    private GameObject humanPlayer, computerPlayer;
    [SerializeField]
    private GameObject playerDeck;
    [SerializeField]
    private GameObject actionsMenu;
    [SerializeField]
    private GameObject skipToggle;

    private JObject jo;
    private Queue eventQueue;
    private bool playing,pendingActions;

    private string turnPhase;
    private string playerRole, computerRole;

    private void Awake()
    {
        ActionController.ResetGame();
        CityController.ResetGame();
        actionsMenu.SetActive(false);

    }

    // Start is called before the first frame update
    void Start()
    {
        eventQueue = new Queue();
        playing = true;
        pendingActions = false;
        StartCoroutine(Request(SERVER + (StaticVariables.pid == null ? "newgame" : "renewgame" + StaticVariables.pid)));
        StartCoroutine(ManageEvents());
    }

    // Update is called once per frame
    void Update()
    {
    }

    public void DoAction(string command)
    {
        LoseFocus();
        ActionController.ResetActions();
        StartCoroutine(Request(SERVER + "game" + StaticVariables.gid + "?pid=" + StaticVariables.pid + "&" + command));
    }

    IEnumerator Request(string url)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        using (www = new WWW(url))
#pragma warning restore CS0618 // Type or member is obsolete
        {
            waitingText.GetComponent<Text>().text = "Thinking...";
            // Request and wait for the desired page.
            yield return www;
            if (www.text.Length == 0)
            {
                string suburl = url.StartsWith("http://")?url.Substring(7):url;
                suburl = suburl.Substring(0, suburl.IndexOf('/'));
                waitingText.GetComponent<Text>().text = "Unable to contact server\n" + suburl + "\nTrying again shortly";
                yield return new WaitForSeconds(10);
                StartCoroutine(Request(url));
                yield break;
            }
            waitingText.GetComponent<Text>().text = "";
            jo = JObject.Parse(www.text);
            if (StaticVariables.pid == null)
            {
                StaticVariables.pid = jo["pid"].Value<string>();
            }
            if (StaticVariables.gid == null)
            {
                StaticVariables.gid = jo["gid"].Value<string>();
            }
            int currentPlayer = jo["current_player"].Value<int>();
            UpdateStateInformation();
            if (url.Contains("newgame"))
            {
                // Reset log
                gameLog.GetComponent<Text>().text = "";
                // Player Roles
                playerRole = jo["players"]["p0"]["role"].Value<string>();
                computerRole = jo["players"]["p1"]["role"].Value<string>();
                GameObject.Find("PlayerText").GetComponent<Text>().text = "Player Role:\n" + playerRole.Replace('_', ' ');
                GameObject.Find("ComputerText").GetComponent<Text>().text = "Computer Role:\n" + computerRole.Replace('_', ' ');
            }
            QueueEvents(jo["game_log"].Value<string>());
            gameLog.GetComponent<Text>().text += jo["game_log"].Value<string>();
            if (currentPlayer == 0 && (turnPhase=="ACTIONS" || turnPhase=="DISCARD"))
            {
                pendingActions = true;
            }
            else if(turnPhase=="INACTIVE")
            {
                waitingText.GetComponent<Text>().text = "";
            }
            else
            {
                DoAction("action=waiting");
            }
        }
    }

    IEnumerator ManageEvents()
    {
        while (playing)
        {
            if (eventQueue.Count == 0)
            {
                if (pendingActions)
                {
                    pendingActions = false;
                    AddActions();
                }else if (turnPhase == "INACTIVE")
                {
                    playing = false;
                }
                yield return new WaitForSeconds(eventTime / 2);
            }
            else
            {
                NextEvent();
                yield return new WaitForSeconds(eventTime);
            }
        }
    }

    // Updated directly from game state
    private void UpdateStateInformation()
    {
        turnPhase = jo["turn_phase"].Value<string>();
        GameObject.Find("TurnText").GetComponent<Text>().text = "Current Turn: " + jo["game_turn"].Value<int>();
        GameObject.Find("PhaseText").GetComponent<Text>().text = "Current phase: " + jo["turn_phase"].Value<string>();
        GameObject.Find("ActionsText").GetComponent<Text>().text = "Actions remaining: " + jo["remaining_actions"].Value<int>();
        GameObject.Find("OutbreakText").GetComponent<Text>().text = "Outbreaks: " + jo["outbreaks"].Value<int>();
        GameObject.Find("InfectionRateText").GetComponent<Text>().text = "Epidemics: " + jo["infections"].Value<int>() + "\nInfection Rate: " + jo["infection_rate"].Value<int>();
        GameObject.Find("PlayerRemainingText").GetComponent<Text>().text = "Remain: " + jo["player_deck"]["cards_left"].Value<int>();
        // Update remaining cubes
        foreach (string color in colors)
        {
            GameObject.Find("CubeStack" + NameTransformation(color)).transform.GetChild(0).GetComponent<Text>().text = jo["disease_cubes"][color].Value<int>().ToString();
        }
        GameObject.Find("InfectionDiscardText").GetComponent<Text>().text = "Infection deck discard:\n" + ColoredString(jo["infection_deck"]["discard"].ToObject<ArrayList>());
        GameObject.Find("PlayerDiscardText").GetComponent<Text>().text = "Player deck discard:\n" + ColoredString(jo["player_deck"]["discard"].ToObject<ArrayList>());
        CityController.ResetQuarantaines();
        ArrayList quarantine = jo["quarantine_cities"].ToObject<ArrayList>();
        foreach (string cityname in quarantine)
        {
            GameObject.Find(cityname).GetComponent<CityController>().AddQuarantaine();
        }
    }

    private string ColoredString(ArrayList cardNames)
    {
        int i = 0;
        string result = "";
        foreach (string card in cardNames)
        {
            GameObject city = GameObject.Find(card);
            result += "<color=#" + ((city == null) ? "208040" : ColorCoding(city.GetComponent<CityController>().GetColor().ToLower())) + ">" + NameTransformation(card) + "</color>" + (++i==cardNames.Count?" ":", "); 
        }
        return result;
    }

    private string ColorCoding(string color)
    {
        switch (color)
        {
            case "black": return "666666";
            case "blue": return "2A7FFF";
            case "red": return "FF2A2A";
            case "yellow": return "FFCC00";
            default: return "FFFFFF";
        }
    }

    private void QueueEvents(string log)
    {
        string[] lines = log.Split('\n');
        for(int i = 0; i < lines.Length; i++)
        {
            if (lines[i].Length == 0) { continue; }
            if (lines[i].StartsWith("Setting")) { continue; }
            eventQueue.Enqueue(lines[i]);
        }
    }

    // Updated through game log processing
    private void NextEvent()
    {
        string eventName = (string)eventQueue.Dequeue();
        string[] tokens = eventName.Split(' ');
        GameObject actingPlayer = (tokens[0] != computerRole) ? humanPlayer : computerPlayer;
        GameObject otherPlayer = (tokens[0] != playerRole) ? humanPlayer : computerPlayer;
        // Animate epidemics, outbreaks, infections, card draws, card discards, actions, infections prevented, medic passive heals, eradications and win/lost
        if (tokens[0] == "Infect")
        {
            // e.g: Infect 3-black at: istanbul
            GameObject.Find(tokens[3]).GetComponent<CityController>().Infect(tokens[1].Substring(2), int.Parse(tokens[1].Substring(0, 1)));
        } else if (tokens[0] == "Epidemic")
        {
            // e.g: Epidemic at: istanbul
            GameObject.Find(tokens[2]).GetComponent<CityController>().Epidemic();
        } else if (tokens[0] == "Outbreak") {
            // e.g: Outbreak at: istanbul
            GameObject.Find(tokens[2]).GetComponent<CityController>().Outbreak();
        } else if (tokens[1] == "drew:")
        {
            if (tokens[2] != "epidemic")
            {
                actingPlayer.GetComponent<PlayerController>().DrawCard(tokens[2], Camera.main.ScreenToWorldPoint(playerDeck.transform.position));
            }
        } else if (tokens[1] == "discarded:")
        {
            actingPlayer.GetComponent<PlayerController>().DiscardCard(tokens[2], Camera.main.ScreenToWorldPoint(playerDeck.transform.position));
        } else if (tokens[1] == "drove" || tokens[1] == "direct" || tokens[1] == "charter" || tokens[1] == "shuttle")
        {
            actingPlayer.GetComponent<PlayerController>().Goto(GameObject.Find(tokens[tokens.Length - 1]));
        } else if (tokens[1].EndsWith("-treated:"))
        {
            actingPlayer.GetComponent<PlayerController>().GetCurrentCity().GetComponent<CityController>().Treat(tokens[2], int.Parse(tokens[1].Substring(0, 1)));
        } else if (tokens[1] == "built") {
            actingPlayer.GetComponent<PlayerController>().GetCurrentCity().GetComponent<CityController>().BuildRS();
        } else if (tokens[1] == "removed")
        {
            // e.g: SCIENTIST removed research station at: istanbul
            GameObject.Find(tokens[5]).GetComponent<CityController>().RemoveRS();
        } else if (tokens[1] == "gave")
        {
            Vector3 position = actingPlayer.GetComponent<PlayerController>().GetCardPosition(tokens[2]);
            actingPlayer.GetComponent<PlayerController>().DiscardCard(tokens[2], Vector3.zero);
            otherPlayer.GetComponent<PlayerController>().DrawCard(tokens[2], position);
        } else if(tokens[1] == "received")
        {
            Vector3 position = otherPlayer.GetComponent<PlayerController>().GetCardPosition(tokens[2]);
            otherPlayer.GetComponent<PlayerController>().DiscardCard(tokens[2], Vector3.zero);
            actingPlayer.GetComponent<PlayerController>().DrawCard(tokens[2], position);
        } else if (tokens[1] == "discovered")
        {
            // e.g: SCIENTIST discovered cure for: black
            GameObject.Find("Cure" + NameTransformation(tokens[4])).GetComponent<CureController>().DiscoverCure(actingPlayer.GetComponent<PlayerController>().GetCurrentCity());
        } else if(tokens[0] == "Infection")
        {
            // e.g: Infection prevented at: istanbul
            GameObject.Find(tokens[3]).GetComponent<CityController>().Prevented();
        } else if(tokens[1] == "healed")
        {
            // e.g: MEDIC healed black at: istanbul"
            GameObject.Find(tokens[4]).GetComponent<CityController>().Heal(tokens[2]);
        } else if (tokens[0] == "Eradicated")
        {
            // e.g: Eradicated yellow disease
            GameObject.Find("Cure" + NameTransformation(tokens[1])).GetComponent<CureController>().EradicateDisease(actingPlayer.GetComponent<PlayerController>().GetCurrentCity());
        }else if (tokens[2] == "LOST")
        {
            CityController.Lost();
            EndEvent("lost");
        }
        else if(tokens[2] == "WON")
        {
            CityController.Won();
            EndEvent("won");
        }

    }

    private void EndEvent(string condition)
    {
        waitingText.GetComponent<Text>().text = "You "+condition+" the game!\nWould you be willing to answer a few short, multiple-choice questions about your experience?";
        actionsMenu.SetActive(true);
        GameObject content = GameObject.Find("ActionsContent");
        foreach (Transform child in content.transform)
        {
            Destroy(child.gameObject);
        }
        GameObject yesButton = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/ActionButton"));
        yesButton.transform.SetParent(content.transform);
        yesButton.GetComponent<ButtonController>().SetEndgame(true);
        GameObject noButton = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/ActionButton"));
        noButton.transform.SetParent(content.transform);
        noButton.GetComponent<ButtonController>().SetEndgame(false);
    }

    private void AddActions()
    {
        if(turnPhase == "ACTIONS")
        {
            AddActionsCity("drive_ferry", "Drive or ferry to: ");
            AddActionsCity("direct_flight", "Direct flight to: ");
            AddActionsCity("charter_flight", "Charter flight to: ");
            AddActionsCity("shuttle_flight", "Shuttle flight to: ");
            //AddActionsPawn("give_knowledge", "receiver", "Give knowledge: ");
            //AddActionsPawn("receive_knowledge", "giver", "Receive knowledge: ");
            AddActionsCard("give_knowledge", "receiver", "Give knowledge: ", humanPlayer);
            AddActionsCard("receive_knowledge", "giver", "Receive knowledge: ", computerPlayer);
            GameObject currentCity = humanPlayer.GetComponent<PlayerController>().GetCurrentCity();
            foreach (JObject possible in jo["actions"]["treat_disease"].ToObject<ArrayList>())
            {
                currentCity.GetComponent<ActionController>().AddAction("Treat disease: " + possible["color"].Value<string>(), "action=treat_disease&color=" + possible["color"].Value<string>());
            }
            foreach (JObject possible in jo["actions"]["build_researchstation"].ToObject<ArrayList>())
            {
                currentCity.GetComponent<ActionController>().AddAction("Build research station" + (possible["replace"].Value<string>() == "none" ? "" : ", remove at: " + NameTransformation(possible["replace"].Value<string>())), "action=build_researchstation&replace=" + possible["replace"].Value<string>());
            }
            foreach (JObject possible in jo["actions"]["discover_cure"].ToObject<ArrayList>())
            {
                string action = "Discover " + possible["color"].Value<string>() + " cure discarding: ", actionURL = "action=discover_cure&color=" + possible["color"].Value<string>() + "&chosen_cards=";
                ArrayList cure_cards = possible["chosen_cards"].ToObject<ArrayList>();
                cure_cards.Sort();
                foreach (string cityname in cure_cards) { action += NameTransformation(cityname) + ", "; actionURL += cityname + "-"; }
                currentCity.GetComponent<ActionController>().AddAction(action.Substring(0, action.Length - 2), actionURL.Substring(0, actionURL.Length - 1));
            }
        }else if(turnPhase == "DISCARD")
        {
            AddActionsCard("discard","discard","Discard: ",humanPlayer);
        }
    }

    private void AddActionsCity(string key,string message)
    {
        foreach(JObject possible in jo["actions"][key].ToObject<ArrayList>())
        {
            string target = possible["target"].Value<string>();
            GameObject.Find(target).GetComponent<ActionController>().AddAction(message + NameTransformation(target), "action=" + key + "&target=" + target);
        }
    }

    // Currently unused since pawns are difficult to click
    private void AddActionsPawn(string key, string key2, string message)
    {
        foreach (JObject possible in jo["actions"][key].ToObject<ArrayList>())
        {
            string target = possible["target"].Value<string>();
            computerPlayer.GetComponent<ActionController>().AddAction(message + NameTransformation(target), "action=" + key + "&target=" + target + "&" + key2 + "=" + possible[key2].Value<string>());
        }
    }

    private void AddActionsCard(string key, string key2, string message, GameObject player)
    {
        foreach (JObject possible in jo["actions"][key].ToObject<ArrayList>())
        {
            string target = possible[(possible["target"] == null ? key : "target")].Value<string>();
            string other = possible["target"] == null ? "" : ("&target=" + target);
            player.GetComponent<PlayerController>().GetCard(target).GetComponent<ActionController>().AddAction(message + NameTransformation(target), "action=" + key + other + "&" + key2 + "=" + possible[key2].Value<string>());
        }
    }

    public static string NameTransformation(string text)
    {
        text = text.Replace('_', ' ');
        string up = text.ToUpper();
        string down = text.ToLower();
        string result = "";
        bool uppercase = true;
        for (int i = 0; i < text.Length; i++)
        {
            result += uppercase ? up[i] : down[i];
            uppercase = text[i] == ' ';
        }
        return result;
    }

    public void Focus(ArrayList actions, ArrayList actionsURLs)
    {
        if(actions.Count == 0)
        {
            if (playing) { LoseFocus(); }
        }
        else if(skipToggle.GetComponent<Toggle>().isOn && actions.Count == 1)
        {
            DoAction((string)(actionsURLs[0]));
        }
        else
        {
            actionsMenu.SetActive(true);
            GameObject content = GameObject.Find("ActionsContent");
            foreach(Transform child in content.transform)
            {
                Destroy(child.gameObject);
            }
            for(int i=0; i < actions.Count; i++)
            {
                GameObject newButton = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/ActionButton"));
                newButton.transform.SetParent(content.transform);
                newButton.GetComponent<ButtonController>().SetText((string)(actions[i]), (string)(actionsURLs[i]));
            }
        }
    }

    public void LoseFocus()
    {
        actionsMenu.SetActive(false);
    }

}
