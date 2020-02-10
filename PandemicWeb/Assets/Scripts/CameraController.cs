using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraController : MonoBehaviour
{
    public float zoomSensitivity;
    public float zoomSpeed;
    public float cameraSpeed;

    [SerializeField]
    private float maximumSize=0;
    [SerializeField]
    private float minimumSize=0;
    private float zoom;
    private float xMax, yMax, sizeX, sizeY;

    // Start is called before the first frame update
    void Start()
    {
        GameObject map = GameObject.Find("Map");
        Sprite sprite = map.GetComponent<SpriteRenderer>().sprite;
        // Initial zoom
        zoom = GetComponent<Camera>().orthographicSize;
        // Maximum (x,y) position for the game's board
        xMax = sprite.rect.width / 200f;
        yMax = sprite.rect.height / 200f;
    }

    // Update is called once per frame
    void Update()
    {
        if (!GameManager.HasFocus() && !(Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl)))
        {
            zoom -= Input.GetAxis("Mouse ScrollWheel") * zoomSensitivity;
            zoom = Mathf.Clamp(zoom, minimumSize, maximumSize);
            if (zoom != GetComponent<Camera>().orthographicSize)
            {
                GetComponent<Camera>().orthographicSize = Mathf.Lerp(GetComponent<Camera>().orthographicSize, zoom, Time.deltaTime * zoomSpeed);
            }
        }
        // Adjust camera sizes
        sizeX = GetComponent<Camera>().orthographicSize * GetComponent<Camera>().aspect;
        sizeY = GetComponent<Camera>().orthographicSize;
        bool moveLeft = (transform.position.x + sizeX) > xMax;
        bool moveRight = (transform.position.x + xMax) < sizeX;
        bool moveDown = (transform.position.y + sizeY) > yMax;
        bool moveUp = (transform.position.y + yMax) < sizeY;
        if ((Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow) || moveUp) && !moveDown)
        {
            transform.Translate(Vector3.up * cameraSpeed * Time.deltaTime);
        }
        if ((Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) || moveLeft) && !moveRight)
        {
            transform.Translate(Vector3.left * cameraSpeed * Time.deltaTime);
        }
        if ((Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow) || moveDown) && !moveUp)
        {
            transform.Translate(Vector3.down * cameraSpeed * Time.deltaTime);
        }
        if ((Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow) || moveRight) && !moveLeft)
        {
            transform.Translate(Vector3.right * cameraSpeed * Time.deltaTime);
        }
    }

}
