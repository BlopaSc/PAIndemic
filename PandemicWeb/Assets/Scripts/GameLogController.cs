using UnityEngine;
using UnityEngine.UI;

public class GameLogController : MonoBehaviour
{
    public void ResetLog()
    {
        this.GetComponent<Text>().text = "";
    }

    public void AddLog(string log)
    {
        RectTransform rt = this.GetComponent<RectTransform>();
        Text text = this.GetComponent<Text>();
        text.text += log;
        rt.sizeDelta = new Vector2(rt.rect.width, text.preferredHeight);
    }
}
