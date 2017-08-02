using UnityEngine;
using System.Collections;

public class Audio : MonoBehaviour {
	private static AudioSource _as;
	//private static string path;
	private static string code;
	// Use this for initialization
	void Start () {
		code = "-1";
		//path = Application.streamingAssetsPath+"/Resources/";
		_as = GameObject.Find("Audios").GetComponent<AudioSource> ();
	}

	public void set_source(string country)
	{
		_as.Stop ();
		if (country == "-1") {
			code = "-1";
			return;
		}
		else {
			code = country;
		}
		_as.clip = Resources.Load<AudioClip>(code);
		_as.Play ();
	}

	public string get_source()
	{
		return code;
	}
	
	// Update is called once per frame
	void Update () {
	
	}
}
