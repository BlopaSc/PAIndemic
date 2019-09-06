using UnityEngine;

public class CubeStackController : MonoBehaviour
{
    private static Sprite[][] coloredBlocks = null;
    private static Vector3 generalOffset = new Vector3(-0.75f,-0.7f,-2.5f);
    private static Vector3 specificOffset = new Vector3(0.5f, 0f, 0f);
    private int color = -1;

    // Start is called before the first frame update
    void Start()
    {
        if(coloredBlocks == null)
        {
            coloredBlocks = new Sprite[4][];
            for(int i = 0; i < coloredBlocks.Length; i++)
            {
                coloredBlocks[i] = Resources.LoadAll<Sprite>("Cubes_" + GameManager.colors[i]);
            }
        }
    }

    public void SetColor(string color)
    {
        for(int i=0; i<4; i++)
        {
            if (color == GameManager.colors[i])
            {
                this.color = i;
            }
        }
    }

    public void SetPosition(Vector3 position,int offset)
    {
        transform.position = position + generalOffset + (offset * specificOffset);
    }

    public void SetInfection(int level)
    {
        GetComponent<SpriteRenderer>().sprite = (level > 0) ? coloredBlocks[color][level - 1] : null;
    }

}
