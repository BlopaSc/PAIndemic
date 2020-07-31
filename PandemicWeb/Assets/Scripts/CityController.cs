using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CityController : MonoBehaviour
{

    private static readonly Vector3 quarantineOffset = new Vector3(0, 0, -0.3f);
    private static readonly Vector3 researchStationOffset = new Vector3(0, 0.5f, -0.5f);
    private static readonly Vector3 textOffset = new Vector3(0, 30f, 0);

    private static ArrayList cities = null;

    private GameObject myCityName = null;
    [SerializeField]
    private GameObject myResearchStation;
    [SerializeField]
    private GameObject myQuarantine;
    [SerializeField]
    private GameObject[] myCubeStacks;
    private int[] cubeCounters;

    // Start is called before the first frame update
    void Start()
    {
        // Name
        myCityName = Instantiate(Resources.Load<GameObject>("Prefabs/CityName"));
        myCityName.transform.SetParent(GameObject.Find("CityNames").transform);
        myCityName.transform.SetAsFirstSibling();
        myCityName.name = "Text_" + transform.name;
        myCityName.GetComponent<Text>().text = GameManager.NameTransformation(transform.name);
        // RS and quarantaine
        if (transform.name != "atlanta") { myResearchStation.GetComponent<SpriteRenderer>().sprite = null; }
        myQuarantine.GetComponent<SpriteRenderer>().sprite = null;
        // Cube stacks
        cubeCounters = new int[myCubeStacks.Length];
        for(int i = 0; i < myCubeStacks.Length; i++)
        {
            cubeCounters[i] = 0;
            myCubeStacks[i].GetComponent<SpriteRenderer>().sprite = null;
        }
        cities.Add(this);
    }

    // Update is called once per frame
    void Update()
    {
        // Updates city name position
        Vector3 position = Camera.main.WorldToScreenPoint(this.transform.position);
        myCityName.transform.position = new Vector3(position.x + textOffset.x, position.y + textOffset.y, 0f);
    }

    public static void ResetGame()
    {
        cities = new ArrayList();
    }

    public static void ResetQuarantaines()
    {
        foreach(CityController city in cities)
        {
            city.myQuarantine.GetComponent<SpriteRenderer>().sprite = null;
        }
    }

    public void AddQuarantaine()
    {
        myQuarantine.GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Images/QuarantineSymbol");
    }

    public void Infect(string color,int number)
    {
        for (int i = 0; i < myCubeStacks.Length; i++)
        {
            if (myCubeStacks[i].transform.name.ToLower().Contains(color))
            {
                Sprite[] coloredBlocks = Resources.LoadAll<Sprite>("Images/Cubes_" + color);
                cubeCounters[i] += number;
                myCubeStacks[i].GetComponent<SpriteRenderer>().sprite = cubeCounters[i] > 0 ? coloredBlocks[cubeCounters[i]-1] : null;
                GameObject infection = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Infection"));
                infection.GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Images/Infection" + GameManager.NameTransformation(color));
                infection.GetComponent<AscendingAnimationScript>().BeginAnimation(transform.gameObject, 5*GameManager.eventTime);
            }
        }
    }

    public void Treat(string color,int number)
    {
        for (int i = 0; i < myCubeStacks.Length; i++)
        {
            if (myCubeStacks[i].transform.name.ToLower().Contains(color))
            {
                Sprite[] coloredBlocks = Resources.LoadAll<Sprite>("Images/Cubes_" + color);
                cubeCounters[i] -= number;
                myCubeStacks[i].GetComponent<SpriteRenderer>().sprite = cubeCounters[i] > 0 ? coloredBlocks[cubeCounters[i] - 1] : null;
                GameObject treatment = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Treatment"));
                treatment.GetComponent<AscendingAnimationScript>().BeginAnimation(transform.gameObject, 2*GameManager.eventTime);
            }
        }
    }

    public void Prevented()
    {
        GameObject prevent = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Prevent"));
        prevent.GetComponent<EnlargeVanishAnimationScript>().BeginAnimation(transform.gameObject, 2*GameManager.eventTime);
    }

    public void Heal(string color)
    {
        for(int i = 0; i < myCubeStacks.Length; i++)
        {
            if (myCubeStacks[i].transform.name.ToLower().Contains(color))
            {
                cubeCounters[i] = 0;
                myCubeStacks[i].GetComponent<SpriteRenderer>().sprite = null;
                GameObject treatment = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Treatment"));
                treatment.GetComponent<AscendingAnimationScript>().BeginAnimation(transform.gameObject, 2*GameManager.eventTime);
            }
        }
    }

    public void Epidemic()
    {
        GameObject epidemic = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Epidemic"));
        epidemic.GetComponent<EnlargeVanishAnimationScript>().BeginAnimation(transform.gameObject, 4*GameManager.eventTime);
    }
    
    public void Outbreak()
    {
        GameObject outbreak = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Outbreak"));
        outbreak.GetComponent<EnlargeVanishAnimationScript>().BeginAnimation(transform.gameObject, 4*GameManager.eventTime);
    }

    public void BuildRS()
    {
        myResearchStation.GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Images/ResearchStation");
        GameObject building = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Build"));
        building.GetComponent<AscendingAnimationScript>().BeginAnimation(transform.gameObject, 2*GameManager.eventTime);
    }

    public void RemoveRS()
    {
        // Consider animation?
        myResearchStation.GetComponent<SpriteRenderer>().sprite = null;
    }

    public string GetColor()
    {
        return transform.parent.transform.name.Substring(4);
    }

    public static void Won()
    {
        foreach (CityController city in cities)
        {
            GameObject won = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Winner"));
            won.GetComponent<EnlargeVanishAnimationScript>().BeginAnimation(city.transform.gameObject, 4 * GameManager.eventTime,0.5f);
        }
    }

    public static void Lost()
    {
        foreach (CityController city in cities)
        {
            GameObject lost = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Loser"));
            lost.GetComponent<EnlargeVanishAnimationScript>().BeginAnimation(city.transform.gameObject, 4 * GameManager.eventTime,0.5f);
        }
    }

}
