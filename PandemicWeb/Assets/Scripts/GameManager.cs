using Newtonsoft.Json.Linq;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class GameManager : MonoBehaviour
{

    public static readonly string[] colors = { "yellow", "red", "blue", "black" };

    public const string SERVER = "http://127.0.0.1:31337/";
#pragma warning disable CS0618 // Type or member is obsolete
    public WWW www=null;
#pragma warning restore CS0618 // Type or member is obsolete

    private static GameObject optionsMenu=null, waitingText=null, gameLogText=null;
    private static bool focused = false;
    private string gid=null, pid=null;

    // Start is called before the first frame update
    void Start()
    {
        if(optionsMenu == null)
        {
            optionsMenu = GameObject.Find("OptionsMenu");
        }
        if (waitingText == null)
        {
            waitingText = GameObject.Find("TextWaiting");
        }
        if (gameLogText == null)
        {
            gameLogText = GameObject.Find("TextGameLog");
            gameLogText.GetComponent<GameLogController>().ResetLog();
        }
        LoseFocus();
        StartCoroutine(Request(SERVER+"newgame"));
    }

    public void DoAction(string command)
    {
        StartCoroutine(Request(SERVER+"game"+gid+ "?pid="+pid+ "&" + command));
    }

    public static string NameTransformation(string text)
    {
        return text.ToUpper()[0] + text.Substring(1).Replace("_", " ");
    }

    IEnumerator Request(string url)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        using (www = new WWW(url))
#pragma warning restore CS0618 // Type or member is obsolete
        {
            waitingText.SetActive(true);
            // Request and wait for the desired page.
            yield return www;
            if (www.text.Length == 0)
            {
                waitingText.SetActive(true);
                waitingText.GetComponent<Text>().text = "Unable to contact server\nTry again later";
                yield break;
            }
            waitingText.SetActive(false);
            JObject jo = JObject.Parse(www.text);
            if (gid==null || pid==null)
            {
                gid = jo["gid"].Value<string>();
                pid = jo["pid"].Value<string>();
            }
            // Updates cure/eradicated states
            foreach(string color in colors)
            {
                GameObject.Find("Objective_" + color).GetComponent<ObjectiveController>().UpdateState(jo["cures"][color].Value<bool>(), jo["eradicated"][color].Value<bool>());
            }
            // Update epidemics, outbreaks, infection rate
            GameObject.Find("TextOutbreaks").GetComponent<Text>().text = "Outbreaks: "+jo["outbreaks"].Value<int>();
            GameObject.Find("TextInfectionRate").GetComponent<Text>().text = "Epidemics: "+jo["infections"].Value<int>()+"\nInfection Rate: " + jo["infection_rate"].Value<int>();
            // Update remaining cubes
            foreach (string color in colors)
            {
                GameObject.Find("Text_" + color + "Stack").GetComponent<Text>().text = jo["disease_cubes"][color].Value<int>().ToString();
            }
            // Updates information regarding player deck, infection deck and player roles
            GameObject.Find("TextPlayerDeck").GetComponent<Text>().text = "Remain: " + jo["player_deck"]["cards_left"].Value<int>();
            ArrayList discarded = jo["infection_deck"]["discard"].ToObject<ArrayList>();
            GameObject.Find("InfectionDeckDiscard").GetComponent<Text>().text = "Discard:\n\n";
            foreach (string discard in discarded)
            {
                GameObject.Find("InfectionDeckDiscard").GetComponent<Text>().text += GameManager.NameTransformation(discard)+", ";
            }
            discarded = jo["player_deck"]["discard"].ToObject<ArrayList>();
            GameObject.Find("PlayerDeckDiscard").GetComponent<Text>().text = "Discard:\n\n";
            foreach(string discard in discarded)
            {
                GameObject.Find("PlayerDeckDiscard").GetComponent<Text>().text += GameManager.NameTransformation(discard) + ", ";
            }
            GameObject.Find("TextTurnInformation").GetComponent<Text>().text = "Player role:\n" + jo["players"]["p0"]["role"].Value<string>().Replace("_"," ") + "\n\nComputer role:\n" + jo["players"]["p1"]["role"].Value<string>().Replace("_", " ") + "\n\n";
            GameObject.Find("TextTurnInformation").GetComponent<Text>().text += "Expecting epidemic:\n"+jo["player_deck"]["epidemic_expectation"].Value<bool>()+"\n\nEpidemic pile left:\n"+ jo["player_deck"]["epidemic_countdown"].Value<int>();
            ArrayList piles = jo["infection_deck"]["known_piles"].ToObject<ArrayList>();
            GameObject.Find("InfectionDeckPiles").GetComponent<Text>().text = "Known infection deck piles:\n\n> Bottom first:\n\n";
            foreach (var pile in piles)
            {
                foreach (string cityname in (JArray)(pile))
                {
                    GameObject.Find("InfectionDeckPiles").GetComponent<Text>().text += GameManager.NameTransformation(cityname) + ", " ;
                }
                GameObject.Find("InfectionDeckPiles").GetComponent<Text>().text += "\n\n";
            }
            // Update game log
            gameLogText.GetComponent<GameLogController>().AddLog(jo["game_log"].Value<string>());
            // Updates city information
            GameObject city;
            ArrayList quarantine = jo["quarantine_cities"].ToObject<ArrayList>();
            foreach (JProperty city_name in jo["cities"])
            {
                city = GameObject.Find(city_name.Name);
                city.GetComponent<CityController>().UpdateInfectionCubes(jo["cities"][city_name.Name]["disease_cubes"]["yellow"].Value<int>(), jo["cities"][city_name.Name]["disease_cubes"]["red"].Value<int>(),jo["cities"][city_name.Name]["disease_cubes"]["blue"].Value<int>(), jo["cities"][city_name.Name]["disease_cubes"]["black"].Value<int>());
                city.GetComponent<CityController>().UpdateResearchStation(jo["cities"][city_name.Name]["research_station"].Value<bool>());
                city.GetComponent<CityController>().UpdateQuarantine(quarantine.Contains(city_name.Name));
                city.GetComponent<ClickActions>().ResetActions();
            }
            // Updates player information and position
            GameObject humanPlayer = GameObject.Find("PlayerPawn");
            GameObject computerPlayer = GameObject.Find("ComputerPawn");
            humanPlayer.GetComponent<PlayerController>().SetLocation(jo["players"]["p0"]["location"].Value<string>());
            computerPlayer.GetComponent<PlayerController>().SetLocation(jo["players"]["p1"]["location"].Value<string>());
            humanPlayer.GetComponent<PlayerController>().SetCards(jo["players"]["p0"]["cards"].ToObject<ArrayList>());
            computerPlayer.GetComponent<PlayerController>().SetCards(jo["players"]["p1"]["cards"].ToObject <ArrayList>());
            humanPlayer.GetComponent<ClickActions>().ResetActions();
            computerPlayer.GetComponent<ClickActions>().ResetActions();
            if (jo["turn_phase"].Value<string>().Equals("ACTIONS"))
            {
                // Update turn information
                GameObject.Find("TextTurn").GetComponent<Text>().text = "Current Turn: " + jo["game_turn"].Value<int>();
                GameObject.Find("TextTurnPhase").GetComponent<Text>().text = "Current phase: ACTIONS";
                GameObject.Find("TextActionsRemaining").GetComponent<Text>().text = "Actions remaining: " + jo["remaining_actions"].Value<int>();

                // Drive ferry actions
                foreach (JObject possible in jo["actions"]["drive_ferry"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    city.GetComponent<ClickActions>().AddAction("Drive ferry to " + city.GetComponent<CityController>().GetCityName(), "action=drive_ferry&target=" + possible["target"].Value<string>());
                }
                // Direct flight actions
                foreach (JObject possible in jo["actions"]["direct_flight"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    city.GetComponent<ClickActions>().AddAction("Direct flight to " + city.GetComponent<CityController>().GetCityName(), "action=direct_flight&target=" + possible["target"].Value<string>());
                }
                // Charter flight actions
                foreach (JObject possible in jo["actions"]["charter_flight"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    city.GetComponent<ClickActions>().AddAction("Charter flight to " + city.GetComponent<CityController>().GetCityName(), "action=charter_flight&target=" + possible["target"].Value<string>());
                }
                // Shuttle flight actions
                foreach (JObject possible in jo["actions"]["shuttle_flight"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    city.GetComponent<ClickActions>().AddAction("Shuttle flight to " + city.GetComponent<CityController>().GetCityName(), "action=shuttle_flight&target=" + possible["target"].Value<string>());
                }
                // Trade cards
                foreach (JObject possible in jo["actions"]["give_knowledge"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    computerPlayer.GetComponent<ClickActions>().AddAction("Give knowledge: " + city.GetComponent<CityController>().GetCityName(), "action=give_knowledge&target=" + possible["target"].Value<string>() + "&receiver=" + possible["receiver"].Value<string>());
                }
                foreach (JObject possible in jo["actions"]["receive_knowledge"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    computerPlayer.GetComponent<ClickActions>().AddAction("Receive knowledge: " + city.GetComponent<CityController>().GetCityName(), "action=receive_knowledge&target=" + possible["target"].Value<string>() + "&giver=" + possible["giver"].Value<string>());
                }
                // Build research station
                city = GameObject.Find(humanPlayer.GetComponent<PlayerController>().GetLocation());
                foreach (JObject possible in jo["actions"]["build_researchstation"].ToObject<ArrayList>())
                {
                    string target = possible["replace"].Value<string>();
                    if (target.Equals("none"))
                    {
                        city.GetComponent<ClickActions>().AddAction("Build research station", "action=build_researchstation&replace=none");
                    }
                    else
                    {
                        GameObject targetCity = GameObject.Find(target);
                        city.GetComponent<ClickActions>().AddAction("Build research station, remove at " + targetCity.GetComponent<CityController>().GetCityName(), "action=build_researchstation&replace=" + target);
                    }
                }
                // Treat disease
                foreach (JObject possible in jo["actions"]["treat_disease"].ToObject<ArrayList>())
                {
                    city.GetComponent<ClickActions>().AddAction("Treat " + possible["color"].Value<string>() + " disease", "action=treat_disease&color=" + possible["color"].Value<string>());
                }
                // Find cure
                foreach (JObject possible in jo["actions"]["discover_cure"].ToObject<ArrayList>())
                {
                    string cities = "", citiesURL = "";
                    bool first = true;
                    foreach (string cityname in possible["chosen_cards"].ToObject<ArrayList>())
                    {
                        if (first)
                        {
                            first = false;
                        }
                        else
                        {
                            cities += ", ";
                            citiesURL += "-";
                        }
                        cities += GameObject.Find(cityname).GetComponent<CityController>().GetCityName();
                        citiesURL += cityname;
                    }
                    city.GetComponent<ClickActions>().AddAction("Discover " + possible["color"].Value<string>() + " cure discarding " + cities, "action=discover_cure&color=" + possible["color"].Value<string>() + "&chosen_cards=" + citiesURL);
                }
                // Rally flight
                foreach (JObject possible in jo["actions"]["rally_flight"].ToObject<ArrayList>())
                {
                    int target = possible["target_player"].Value<int>();
                    int player = possible["player"].Value<int>();
                    string playerrole = jo["players"]["p" + player.ToString()]["role"].Value<string>().Replace("_", " ");
                    GameObject targetPlayer=null;
                    switch (target)
                    {
                        case 0:
                            targetPlayer = humanPlayer;
                            break;
                        case 1:
                            targetPlayer = computerPlayer;
                            break;
                    }
                    city = GameObject.Find(targetPlayer.GetComponent<PlayerController>().GetLocation());
                    targetPlayer.GetComponent<ClickActions>().AddAction("Rally flight " + playerrole + " to " + city.GetComponent<CityController>().GetCityName(), "action=rally_flight&player=" + player.ToString() + "&target_player=" + target.ToString());

                }
                // Special charter flight
                foreach (JObject possible in jo["actions"]["special_charter_flight"].ToObject<ArrayList>())
                {
                    city = GameObject.Find(possible["target"].Value<string>());
                    city.GetComponent<ClickActions>().AddAction("Special charter flight to "+ city.GetComponent<CityController>().GetCityName()+" discarding "+NameTransformation(possible["discard"].Value<string>()), "action=special_charter_flight&target="+possible["target"].Value<string>() + "&discard="+possible["discard"].Value<string>());
                }
            }
            else if (jo["turn_phase"].Value<string>().Equals("DISCARD"))
            {
                // Update actions remaining
                GameObject.Find("TextTurnPhase").GetComponent<Text>().text = "Current phase: DISCARD";
                GameObject.Find("TextActionsRemaining").GetComponent<Text>().text = "Actions remaining: " + jo["remaining_actions"].Value<int>();
                foreach(JObject possible in jo["actions"]["discard"].ToObject<ArrayList>())
                {
                    humanPlayer.GetComponent<ClickActions>().AddAction("Discard card "+NameTransformation(possible["discard"].Value<string>()),"action=discard&discard="+ possible["discard"].Value<string>());
                }
            }
            else if (jo["turn_phase"].Value<string>().Equals("NEW"))
            {
                // Update actions remaining
                GameObject.Find("TextTurnPhase").GetComponent<Text>().text = "Current phase: WAITING";
                DoAction("action=finish_turn");
            }
            else if (jo["turn_phase"].Value<string>().Equals("INACTIVE"))
            {
                GameObject.Find("TextTurnPhase").GetComponent<Text>().text = "Current phase: "+ jo["game_state"].Value<string>();
                waitingText.SetActive(true);
                if (jo["game_state"].Value<string>().Equals("LOST"))
                {
                    waitingText.GetComponent<Text>().text = "You lost the game!\nPlease fill the questionnaire";

                }
                else if (jo["game_state"].Value<string>().Equals("WIN"))
                {
                    waitingText.GetComponent<Text>().text = "You won the game!\nPlease fill the questionnaire";
                }
                else
                {
                    waitingText.GetComponent<Text>().text = "UNDEFINED BEHAVIOUR";
                    Debug.Log(jo);
                    Debug.Log("Undocumented game state");
                }
            }
            else
            {
                Debug.Log(jo);
                Debug.Log("Undocumented game phase");
            }
        }
    }

    public static bool HasFocus()
    {
        return focused;
    }

    public static void Focus(GameObject newFocus, ArrayList actions, ArrayList actionsURLs)
    {
        if (optionsMenu != null)
        {
            optionsMenu.SetActive(true);
            GameObject menuContent = GameObject.Find("OptionsMenuContent");
            int children = menuContent.transform.childCount;
            for (int i = 0; i < children; i++)
            {
                GameObject.Destroy(menuContent.transform.GetChild(i).gameObject);
            }
            for (int i=0; i < actions.Count; i++)
            {
                GameObject newButton = GameObject.Instantiate(Resources.Load<GameObject>("ActionButton"));
                newButton.SetActive(true);
                newButton.transform.SetParent(menuContent.transform);
                newButton.GetComponent<ButtonController>().SetText((string)(actions[i]),(string)(actionsURLs[i]));
            }
        }
        focused = true;
    }

    public static void LoseFocus()
    {
        if (optionsMenu != null)
        {
            GameObject menuContent = GameObject.Find("OptionsMenuContent");
            if (menuContent != null)
            {
                int children = menuContent.transform.childCount;
                for (int i = 0; i < children; i++)
                {
                    GameObject.Destroy(menuContent.transform.GetChild(i).gameObject);
                }
            }
            optionsMenu.SetActive(false);
        }
        focused = false;
    }

}
