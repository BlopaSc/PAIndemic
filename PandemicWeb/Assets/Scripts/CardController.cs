using UnityEngine;
using UnityEngine.UI;

public class CardController : MonoBehaviour
{
    private static Vector3 offset = new Vector3(150f, 0f, 0f);
    private static Vector3 backrowOffset = new Vector3(70f, 30f, 0f);
    private Vector3 position;

    [SerializeField]
    private GameObject myText=null;

    public void SetName(string newName)
    {
        myText.GetComponent<Text>().text = GameManager.NameTransformation(newName);
        GetComponent<Image>().sprite = Resources.Load<Sprite>("Card"+GameObject.Find(newName).GetComponent<SpriteRenderer>().sprite.name.Substring(4));
    }

    public static Vector3 GetPosition(int num) {
        // return new Vector3((offset.x * (num >> 1)) + ((num % 2) * backrowOffset.x), backrowOffset.y * (num % 2), 0f);
        return (offset * (num / 2)) + (backrowOffset * (num % 2));
    }

}
