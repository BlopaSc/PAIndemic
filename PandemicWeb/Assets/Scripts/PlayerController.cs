using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PlayerController : MonoBehaviour
{

    [SerializeField]
    private GameObject myCanvas = null;

    [SerializeField]
    private Vector3 positionOffset = new Vector3(0,0,0);
    private string location;

    private ArrayList myCards;
    
    

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
        int counter = 0;
        ArrayList removeList = new ArrayList();
        foreach(string card in this.myCards)
        {
            if(!newCards.Contains(card))
            {
                GameObject.Destroy(GameObject.Find("Card_" + card));
                removeList.Add(card);
            }
            else
            {
                GameObject.Find("Card_" + card).GetComponent<CardController>().SetPosition(counter);
                counter++;
            }
        }
        foreach(string card in removeList)
        {
            this.myCards.Remove(card);
        }
        foreach(string card in newCards)
        {
            if (!this.myCards.Contains(card))
            {
                GameObject newCard = GameObject.Instantiate(Resources.Load<GameObject>("Card"));
                newCard.GetComponent<RectTransform>().SetParent(this.myCanvas.GetComponent<RectTransform>());
                newCard.transform.localScale = Vector3.one;
                newCard.name = "Card_" + card;
                newCard.GetComponent<CardController>().SetName(card);
                newCard.GetComponent<CardController>().SetPosition(counter);
                this.myCards.Add(card);
                counter++;
            }
        }
    }

    public string GetLocation()
    {
        return this.location;
    }

}
