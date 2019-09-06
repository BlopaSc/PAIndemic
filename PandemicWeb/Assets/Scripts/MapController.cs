using UnityEngine;
using UnityEngine.EventSystems;

public class MapController : MonoBehaviour
{
    void OnMouseDown()
    {
        if (EventSystem.current.IsPointerOverGameObject())
        {
            return;
        }
        GameManager.LoseFocus();
    }
}
