using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PlayerController : MonoBehaviour
{
    [SerializeField]
    private Vector3 positionOffset = new Vector3(0,0,0);
    private string location;

    private ArrayList myCards;

    [SerializeField]
    private GameObject myCanvasFirstRow = null;
    [SerializeField]
    private GameObject myCanvasSecondRow = null;


    // Start is called before the first frame update
    void Start()
    {
        this.myCards = new ArrayList();
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void SetLocation(string newLocation)
    {
        GameObject city = GameObject.Find(newLocation);
        if(city != null)
        {
            this.location = newLocation;
            this.transform.position = city.transform.position + this.positionOffset;
        }
    }

    public void SetCards(ArrayList newCards)
    {
        
        ArrayList removeList = new ArrayList();
        foreach(string card in this.myCards)
        {
            if(!newCards.Contains(card))
            {
                GameObject.Destroy(GameObject.Find("Card_" + card));
                removeList.Add(card);
            }
        }
        foreach(string card in removeList)
        {
            this.myCards.Remove(card);
        }
        newCards.Sort();
        int counter = 0;
        foreach(string card in newCards)
        {
            if (!this.myCards.Contains(card))
            {
                GameObject newCard = GameObject.Instantiate(Resources.Load<GameObject>("Card"), ((counter % 2 == 0) ? this.myCanvasFirstRow : this.myCanvasSecondRow).transform);
                newCard.name = "Card_" + card;
                newCard.GetComponent<CardController>().SetName(card);
                newCard.GetComponent<RectTransform>().transform.localScale = Vector3.one;
                newCard.GetComponent<RectTransform>().localPosition = CardController.GetPosition(counter++);
                this.myCards.Add(card);
            }
            else
            {
                GameObject.Find("Card_" + card).transform.SetParent(((counter % 2 == 0) ? this.myCanvasFirstRow : this.myCanvasSecondRow).transform);
                GameObject.Find("Card_" + card).GetComponent<RectTransform>().localPosition = CardController.GetPosition(counter++);
            }
        }
    }

    public void ResetCards()
    {
        foreach (string card in this.myCards)
        {
            GameObject.Find("Card_" + card).GetComponent<ClickActions>().ResetActions();
        }
    }

    public string GetLocation()
    {
        return this.location;
    }

}
