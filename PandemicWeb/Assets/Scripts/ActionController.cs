using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

public class ActionController : MonoBehaviour
{

    private static ArrayList objects = null;

    [SerializeField]
    private GameObject myGlow = null;

    private ArrayList myActions;
    private ArrayList myActionsURLs;

    // Start is called before the first frame update
    void Start()
    {
        myActions = new ArrayList();
        myActionsURLs = new ArrayList();
        if (myGlow != null)
        {
            myGlow.SetActive(false);
            objects.Add(this);
        }
    }

    public static void ResetGame()
    {
        objects = new ArrayList();
    }

    public static void ResetActions()
    {
        foreach(ActionController obj in objects)
        {
            obj.myGlow.SetActive(false);
            obj.myActions.Clear();
            obj.myActionsURLs.Clear();
        }
    }

    public void AddAction(string action,string actionURL)
    {
        if (myActions.Count == 0)
        {
            myGlow.SetActive(true);
        }
        myActions.Add(action);
        myActionsURLs.Add(actionURL);
    }

    private void OnMouseDown()
    {
        PointerEventData pe = new PointerEventData(EventSystem.current);
        pe.position = Input.mousePosition;
        List<RaycastResult> hits = new System.Collections.Generic.List<RaycastResult>();
        EventSystem.current.RaycastAll(pe, hits);
        foreach (RaycastResult h in hits)
        {
            if (h.gameObject.name.StartsWith("ActionButton"))
            {
                return;
            }
        }
        if (transform.name == "Map") {
            Vector2 rayPos = new Vector2(Camera.main.ScreenToWorldPoint(Input.mousePosition).x, Camera.main.ScreenToWorldPoint(Input.mousePosition).y);
            RaycastHit2D[] hitWorld = Physics2D.RaycastAll(rayPos, Vector2.zero, 0f, LayerMask.GetMask("Interactive"));
            foreach(RaycastHit2D hit in hitWorld)
            {
                hit.transform.GetComponent<ActionController>().OnMouseDown();
            }
            if (hitWorld.Length > 0) { return; }
        }
        GameObject.Find("GameManager").GetComponent<GameManager>().Focus(myActions,myActionsURLs);
    }

}
