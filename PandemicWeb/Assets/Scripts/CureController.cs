using UnityEngine;
using UnityEngine.UI;

public class CureController : MonoBehaviour
{
    [SerializeField]
    private Sprite diseaseImage = null;
    [SerializeField]
    private Sprite cureImage = null;
    [SerializeField]
    private Sprite eradicatedImage = null;
    // Start is called before the first frame update
    void Start()
    {
        GetComponent<Image>().sprite = diseaseImage;
    }

    public void DiscoverCure(GameObject cityDiscovered)
    {
        GameObject discover = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Discover"));
        discover.GetComponent<AscendingAnimationScript>().BeginAnimation(cityDiscovered.transform.gameObject, GameManager.eventTime);
        GetComponent<Image>().sprite = cureImage;
    }

    public void EradicateDisease(GameObject cityEradicated)
    {
        GameObject eradicate = GameObject.Instantiate(Resources.Load<GameObject>("Prefabs/Eradicate"));
        eradicate.GetComponent<AscendingAnimationScript>().BeginAnimation(cityEradicated.transform.gameObject, GameManager.eventTime);
        GetComponent<Image>().sprite = eradicatedImage;
    }

}
