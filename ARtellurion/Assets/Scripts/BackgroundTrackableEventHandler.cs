using UnityEngine;
using System.Collections;
using Vuforia;

public class BackgroundTrackableEventHandler : MonoBehaviour,
											   ITrackableEventHandler
{
	#region PRIVATE_MEMBER_VARIABLES

	private TrackableBehaviour mTrackableBehaviour;

	#endregion // PRIVATE_MEMBER_VARIABLES

	public Transform prefab;


	#region UNTIY_MONOBEHAVIOUR_METHODS

	void Start()
	{
		mTrackableBehaviour = GetComponent<TrackableBehaviour>();
		if (mTrackableBehaviour)
		{
			mTrackableBehaviour.RegisterTrackableEventHandler(this);
		}
	}

	#endregion // UNTIY_MONOBEHAVIOUR_METHODS



	#region PUBLIC_METHODS

	/// <summary>
	/// Implementation of the ITrackableEventHandler function called when the
	/// tracking state changes.
	/// </summary>
	public void OnTrackableStateChanged(
		TrackableBehaviour.Status previousStatus,
		TrackableBehaviour.Status newStatus)
	{
		if (newStatus == TrackableBehaviour.Status.DETECTED ||
			newStatus == TrackableBehaviour.Status.TRACKED ||
			newStatus == TrackableBehaviour.Status.EXTENDED_TRACKED)
		{
			OnTrackingFound();
		}
		else
		{
			OnTrackingLost();
		}
	}

	#endregion // PUBLIC_METHODS



	#region PRIVATE_METHODS


	private void OnTrackingFound()
	{
		Transform obj = GameObject.FindWithTag ("Model").transform;
		if (obj != null) {
			obj.parent = mTrackableBehaviour.transform;
			obj.localPosition = new Vector3(0f, 0f, 0f);
			obj.localRotation = Quaternion.Euler(new Vector3(0f,270f,90f));
			//obj.localScale = new Vector3(0.2f, 0.2f, 0.2f);
		}
		Debug.Log("Custom Trackable " + mTrackableBehaviour.TrackableName + " found");
	}


	private void OnTrackingLost()
	{
		Transform obj = GameObject.FindWithTag ("Model").transform;
		if (obj != null) {
			obj.parent = GameObject.FindWithTag ("MainCamera").transform;
			obj.localPosition = new Vector3(0.2f, 0f, 0.9f);
			obj.localRotation = Quaternion.Euler(new Vector3(0f,270f,90f));
			//obj.localScale = new Vector3(0.05f, 0.05f, 0.05f);
		}
		Debug.Log("Trackable " + mTrackableBehaviour.TrackableName + " lost");
	}

	#endregion // PRIVATE_METHODS
}
