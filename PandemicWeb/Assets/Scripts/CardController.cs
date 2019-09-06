using UnityEngine;
using UnityEngine.UI;

public class CardController : MonoBehaviour
{
    private static Vector3 offset = new Vector3(150f, 0f, 0f);

    [SerializeField]
    private GameObject myText=null;

    public void SetName(string newName)
    {
        myText.GetComponent<Text>().text = GameManager.NameTransformation(newName);
        GetComponent<Image>().sprite = Resources.Load<Sprite>("Card"+GameObject.Find(newName).GetComponent<SpriteRenderer>().sprite.name.Substring(4));
    }

    public void SetPosition(int num)
    {
        this.GetComponent<RectTransform>().localPosition = ((float)(num) * offset);
    }

}
