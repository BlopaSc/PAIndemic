using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class MessageManager : MonoBehaviour
{
    private static ArrayList queue = new ArrayList();
    public static readonly int maxMessages = 7;
    public static readonly float timeBetweenMessages = 0.5f;
    private ArrayList messagesTimes;
    private float lastMessage;
    // Start is called before the first frame update
    void Start()
    {
        messagesTimes = new ArrayList();
        for(int i=0; i<maxMessages; i++)
        {
            messagesTimes.Add(0f);
        }
        lastMessage = 0f;
    }

    // Update is called once per frame
    void Update()
    {
        if (Time.time - lastMessage >= timeBetweenMessages)
        {
            for (int i = 0; i < maxMessages && queue.Count > 0; i++)
            {
                if ((float)(messagesTimes[i]) <= Time.time)
                {
                    string msg = queue[0].ToString();
                    GameObject message = GameObject.Instantiate(Resources.Load<GameObject>("WarningText"));
                    message.transform.SetParent(GameObject.Find("Messages").transform);
                    message.GetComponent<Text>().text = msg;
                    message.GetComponent<MessageAnimator>().msgnum = i;
                    queue.RemoveAt(0);
                    messagesTimes[i] = Time.time + (1.8f * MessageAnimator.visible);
                    lastMessage = Time.time;
                    break;
                }
            }
        }
    }

    public static void AddMessages(string[] messages)
    {
        string modified;
        foreach (string message in messages)
        {
            if (message.Length < 5) { continue; }
            if (message.StartsWith("Turn begin")) { continue; }
            modified = message;
            if(modified[1]>='A' && modified[1]<='Z')
            {
                modified = GameManager.NameTransformation(modified.Substring(0,modified.IndexOf(' '))) + modified.Substring(modified.IndexOf(' '));
                if(modified.Contains("to:") || modified.Contains("from:") || modified.Contains("at:") || modified.Contains("discarded:"))
                {
                    modified = modified.Substring(0, modified.LastIndexOf(':')+2) + GameManager.NameTransformation(modified.Substring(modified.LastIndexOf(':')+2));
                }
                if(modified.Contains(" gave "))
                {
                    int first = modified.IndexOf(" gave ") + 6;
                    int second = modified.IndexOf(" to:");
                    modified = modified.Substring(0, first) + GameManager.NameTransformation(modified.Substring(first, second-first)) + modified.Substring(second);
                }
                if(modified.Contains(" received "))
                {
                    int first = modified.IndexOf(" received ") + 10;
                    int second = modified.IndexOf(" from:");
                    modified = modified.Substring(0, first) + GameManager.NameTransformation(modified.Substring(first, second - first)) + modified.Substring(second);
                }
            }else if(modified.StartsWith("Infect") || modified.StartsWith("Outbreak"))
            {
                modified = modified.Substring(0, modified.LastIndexOf(':') + 2) + GameManager.NameTransformation(modified.Substring(modified.LastIndexOf(':') + 2));
            }
            queue.Add(modified);
        }
    }
}
