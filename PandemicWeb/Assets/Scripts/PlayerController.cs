using System;
using UnityEngine;
using UnityEngine.UI;

public class PlayerController : MonoBehaviour
{
    [SerializeField]
    private GameObject currentCity;
    [SerializeField]
    private Vector3 offset;
    [SerializeField]
    private GameObject myCardGroup;

    private Vector3 fromLocation, toLocation;
    private float tStart;
    private bool moving;

    // Start is called before the first frame update
    void Start()
    {
        moving = false;
        transform.position = currentCity.transform.position + offset;
    }

    // Update is called once per frame
    void Update()
    {
        if (moving)
        {
            float ttime = (Time.time - tStart) / GameManager.eventTime;
            transform.position = Vector3.Lerp(fromLocation, toLocation, ttime);
            if (ttime >= 1.0)
            {
                moving = false;
            }
        }
    }

    public void DrawCard(string name, Vector3 from)
    {
        myCardGroup.GetComponent<CardGroupController>().DrawCard(name, from);
    }

    public void DiscardCard(string name, Vector3 to)
    {
        myCardGroup.GetComponent<CardGroupController>().DiscardCard(name, to);
    }

    public void Goto(GameObject to)
    {
        currentCity = to;
        fromLocation = transform.position;
        toLocation = currentCity.transform.position + offset;
        tStart = Time.time;
        moving = true;
    }

    public GameObject GetCurrentCity()
    {
        return currentCity;
    }

    public GameObject GetCard(string name)
    {
        return myCardGroup.GetComponent<CardGroupController>().GetCard(name);
    }

    public Vector3 GetCardPosition(string name)
    {
        return myCardGroup.GetComponent<CardGroupController>().GetCardPosition(name);
    }

}
