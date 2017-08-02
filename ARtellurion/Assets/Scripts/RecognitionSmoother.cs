using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System;

public class RecognitionSmoother : MonoBehaviour {
	private static int size=5;
	private static int[] q=new int[size];
	private static int idx;


	// Use this for initialization
	void Start () {
		idx = 0;
		for (int i = 0; i < size; i++)
			q [i] = -1;
	}

	public static void enqueue(int code)
	{
		q[idx] = code;
		idx = (idx + 1) % size;

	}

	public static int most_common()
	{
		var d = new Dictionary<int,int>();
		int max_code = -1;
		int max_cnt = -1;
		for (int i = 0; i < size; i++) {
			if (d.ContainsKey (q [i]))
				d [q [i]]++;
			else
				d.Add (q [i], 0);
		}
		foreach (var item in d)
			if (item.Value > max_cnt) {
				max_code = item.Key;
				max_cnt = item.Value;
			}
		return max_code;
	}

	// Update is called once per frame
	void Update () {
	
	}
}
