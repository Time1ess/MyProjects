﻿using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System;

public class CountryMap : MonoBehaviour {

	public static Dictionary<string, string> countries;
	public static Dictionary<string, string> codes;
	// Use this for initialization
	void Start () {
		countries = new Dictionary<string, string> ();
		codes = new Dictionary<string, string> ();
		StreamReader sr = null;
		string path;
		try {
			path = Application.streamingAssetsPath+"/";
			sr=File.OpenText(path+"countries.txt");
		}
		catch(Exception ex) {
			Debug.Log (ex.ToString());
			return;
		}
		string line;
		string[] key_value;
		while ((line = sr.ReadLine ()) != null) {
			//Debug.Log (line);
			key_value = line.Split(' ');
			//Debug.Log (key_value [0] + key_value [1]);
			countries.Add (key_value [0], key_value [1]);
			codes.Add (key_value [1], key_value [0]);
		}
		sr.Close ();
		sr.Dispose ();
	}
	
	// Update is called once per frame
	void Update () {
	
	}
}
