using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ModelDisplay : MonoBehaviour {
	public Vector3 display_pos = new Vector3(1, -41, 432);

	private GameObject display_obj;
	private int code = -1;

	public GameObject[] models;

	// Use this for initialization
	void Start () {
		//obj = GameObject.Instantiate (models [16]);
		//
	}

	// Update is called once per frame
	void Update () {
		
	}

	public int get_source()
	{
		return code;
	}

	public void set_source(int code)
	{
		if (this.code != code) {
			this.code = code;
			Destroy (display_obj);
			display_obj = null;
		} else
			return;
		if (code != -1 && models [code]) {
			display_obj = GameObject.Instantiate (models [code]);
			display_obj.transform.GetChild(0).gameObject.AddComponent<SelfRotate>();
		}
	}

}
