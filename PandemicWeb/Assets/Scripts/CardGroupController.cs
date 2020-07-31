using System;
using UnityEngine;
using UnityEngine.UI;

public class CardGroupController : MonoBehaviour
{
    [SerializeField]
    private float verticalDistance, horizontalDistance;
    [SerializeField]
    private Vector3 offset;

    public static readonly int maxCards = 9;

    private GameObject[] cards;
    private string[] names;
    private int numberCards;

    private GameObject movingCard;
    private Vector3 fromLocation, toLocation;
    private float tStart;
    private bool moving,discard;

    // Start is called before the first frame update
    void Start()
    {
        moving = false;
        discard = false;
        numberCards = 0;
        cards = new GameObject[maxCards];
        names = new string[maxCards];
        for(int i = 0; i < maxCards; i++)
        {
            cards[i] = Instantiate(Resources.Load<GameObject>("Prefabs/Card"));
            cards[i].transform.SetParent(transform);
            cards[i].name = "Card" + i;
            cards[i].transform.position = offset + verticalDistance * (i % 2) * (Vector3.up + Vector3.forward) + horizontalDistance * i * Vector3.right;
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (moving)
        {
            float ttime = (Time.time - tStart) / GameManager.eventTime;
            movingCard.transform.position = Vector3.Lerp(fromLocation, toLocation, ttime);
            if (ttime >= 1.0)
            {
                moving = false;
                if (discard){
                    cards[numberCards].GetComponent<SpriteRenderer>().enabled = false;
                    cards[numberCards].transform.GetChild(0).transform.GetChild(0).GetComponent<Text>().text = "";
                    OrganizeCards();
                }
            }
        }
    }

    public void DrawCard(string name, Vector3 from)
    {
        names[numberCards] = name;
        cards[numberCards].GetComponent<SpriteRenderer>().enabled = true;
        numberCards++;
        Array.Sort<string>(names, 0, numberCards);
        int index = (name != "") ? Array.IndexOf(names, name, 0, numberCards) : -1;
        for (int i = 0; i < numberCards; i++)
        {
            cards[i].GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Images/Card" + GameObject.Find(names[i]).GetComponent<CityController>().GetColor());
            cards[i].transform.GetChild(0).transform.GetChild(0).GetComponent<Text>().text = GameManager.NameTransformation(names[i]);
            cards[i].transform.position = i == index ? from : offset + verticalDistance * (i % 2) * (Vector3.up + Vector3.forward) + horizontalDistance * i * Vector3.right;
        }
        tStart = Time.time;
        fromLocation = from;
        toLocation = offset + verticalDistance * (index % 2) * (Vector3.up + Vector3.forward) + horizontalDistance * index * Vector3.right;
        movingCard = cards[index];
        discard = false;
        moving = true;
    }

    public void DiscardCard(string name, Vector3 to)
    {
        int index = Array.IndexOf(names, name, 0, numberCards);
        numberCards--;
        for (int i=index; i < numberCards; i++)
        {
            names[i] = names[i+1];
        }
        if (to != Vector3.zero)
        {
            tStart = Time.time;
            fromLocation = cards[index].transform.position;
            toLocation = to;
            movingCard = cards[index];
            discard = true;
            moving = true;
        }
        else
        {
            cards[numberCards].GetComponent<SpriteRenderer>().enabled = false;
            cards[numberCards].transform.GetChild(0).transform.GetChild(0).GetComponent<Text>().text = "";
            OrganizeCards();
        }
    }

    public void OrganizeCards()
    {
        for (int i = 0; i < numberCards; i++)
        {
            cards[i].GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Images/Card" + GameObject.Find(names[i]).GetComponent<CityController>().GetColor());
            cards[i].transform.GetChild(0).transform.GetChild(0).GetComponent<Text>().text = GameManager.NameTransformation(names[i]);
            cards[i].transform.position = offset + verticalDistance * (i % 2) * (Vector3.up + Vector3.forward) + horizontalDistance * i * Vector3.right;
        }
    }


    public GameObject GetCard(string name)
    {
        for (int i = 0; i < numberCards; i++)
        {
            if (names[i] == name) { return cards[i]; }
        }
        return null;
    }

    public Vector3 GetCardPosition(string name)
    {
        for(int i=0; i < numberCards; i++)
        {
            if (names[i] == name) { return cards[i].transform.position; }
        }
        return Vector3.zero;
    }

}
