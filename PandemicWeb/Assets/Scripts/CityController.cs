using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CityController : MonoBehaviour
{
    private static readonly Vector3 quarantineOffset = new Vector3(0,0,-0.3f);
    private static readonly Vector3 researchStationOffset = new Vector3(0,0.5f,-0.5f);
    private static readonly Vector3 textOffset = new Vector3(0,40f,0);
    private static GameObject canvas = null;
    [SerializeField]
    private string cityName="";
    private GameObject myCityName = null;
    private GameObject myResearchStation = null;
    private GameObject myQuarantine = null;
    private GameObject[] myCubeStacks;
    private bool hasResearchStation = false;
    private bool hasQuarantine = false;
    // Start is called before the first frame update
    void Start()
    {
        if (canvas == null)
        {
            canvas = GameObject.Find("CityTexts");
        }
        this.myCityName = GameObject.Instantiate(Resources.Load<GameObject>("CityName"));
        this.myCityName.transform.SetParent(canvas.transform);
        this.myCityName.transform.SetAsFirstSibling();
        this.myCityName.name = "Text_" + this.name;
        this.myCityName.GetComponent<Text>().text = this.cityName;
        this.myCubeStacks = new GameObject[4];
        for(int i=0; i<4; i++)
        {
            this.myCubeStacks[i] = GameObject.Instantiate(Resources.Load<GameObject>("CubeStack"));
            this.myCubeStacks[i].transform.SetParent(this.transform);
            this.myCubeStacks[i].name =  GameManager.colors[i]+"Stack_" + this.name;
            this.myCubeStacks[i].GetComponent<CubeStackController>().SetColor(GameManager.colors[i]);
            this.myCubeStacks[i].GetComponent<CubeStackController>().SetPosition(this.transform.position,i);
        }
    }

    // Update is called once per frame
    void Update()
    {
        // Updates city name position
        Vector3 position = Camera.main.WorldToScreenPoint(this.transform.position);
        this.myCityName.transform.position = new Vector3(position.x+textOffset.x,position.y+textOffset.y,0f);
    }

    public string GetCityName()
    {
        return cityName;
    }

    public void UpdateInfectionCubes(int yellow, int red, int blue, int black)
    {
        for (int i = 0; i < 4; i++)
        {
            switch (GameManager.colors[i])
            {
                case "yellow":
                    this.myCubeStacks[i].GetComponent<CubeStackController>().SetInfection(yellow);
                    break;
                case "red":
                    this.myCubeStacks[i].GetComponent<CubeStackController>().SetInfection(red);
                    break;
                case "blue":
                    this.myCubeStacks[i].GetComponent<CubeStackController>().SetInfection(blue);
                    break;
                case "black":
                    this.myCubeStacks[i].GetComponent<CubeStackController>().SetInfection(black);
                    break;
            }
        }
    }

    public void UpdateResearchStation(bool build)
    {
        if (build)
        {
            this.BuildResearchStation();
        }
        else
        {
            this.RemoveResearchStation();
        }
    }

    private void BuildResearchStation()
    {
        if (!this.hasResearchStation)
        {
            this.hasResearchStation = true;
            this.myResearchStation = GameObject.Instantiate(Resources.Load<GameObject>("ResearchStation"));
            this.myResearchStation.transform.SetParent(this.transform);
            this.myResearchStation.name = "RS_" + this.name;
            this.myResearchStation.transform.position = this.transform.position + researchStationOffset;
        }
    }

    private void RemoveResearchStation()
    {
        if (this.hasResearchStation)
        {
            this.hasResearchStation = false;
            GameObject.Destroy(this.myResearchStation);
            this.myResearchStation = null;
        }
    }

    public void UpdateQuarantine(bool quarantined)
    {
        if (quarantined)
        {
            this.AddQuarantine();
        }
        else
        {
            this.RemoveQuarantine();
        }
    }

    private void AddQuarantine()
    {
        if (!this.hasQuarantine)
        {
            this.hasQuarantine = true;
            this.myQuarantine = GameObject.Instantiate(Resources.Load<GameObject>("QuarantineArea"));
            this.myQuarantine.transform.SetParent(this.transform);
            this.myQuarantine.name = "QA_" + this.name;
            this.myQuarantine.transform.position = this.transform.position + quarantineOffset;
        }
    }

    private void RemoveQuarantine()
    {
        if (this.hasQuarantine)
        {
            this.hasQuarantine = false;
            GameObject.Destroy(this.myQuarantine);
            this.myQuarantine = null;
        }
    }

}
