using UnityEngine;
using System.Collections;

public class Buttons : MonoBehaviour {
	private static AudioSource _as;
	private static UnityEngine.UI.Text _text;
	// Use this for initialization
	void Start () {
		_as = GameObject.Find("Audios").GetComponent<AudioSource> ();
	}
	
	// Update is called once per frame
	void Update () {
	
	}

	public void click()
	{
		_as.Stop ();
	}
}
