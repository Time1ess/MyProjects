using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using Vuforia;
using System.Diagnostics;
using System.Threading;
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;


public class Recognition : MonoBehaviour {

	#if UNITY_IPHONE && !UNITY_EDITOR
	[DllImport ("__Internal")]
	#else
	[DllImport ("libtellurion")]
	#endif
	private static extern int predict (byte[] image, int origin_heigt, int origin_width, int minHessian, int height, 
		int width, string multi_class_model_path, string one_class_model_path, string dict_path, double threshold, ref double prob);

	private bool mAccessCameraImage = true;

	// The desired camera image pixel format
	private Image.PIXEL_FORMAT mPixelFormat = Image.PIXEL_FORMAT.GRAYSCALE;// or RGBA8888, RGB888, RGB565, YUV
	// Boolean flag telling whether the pixel format has been registered
	private bool mFormatRegistered = false;

	private float delta;
	private static Mutex mutex;
	private int country_code;

	private UnityEngine.UI.Text text;
	private static Audio audio;
	private ModelDisplay model_display;

	private string path;
	private double prob;
	private Stopwatch sw;

	private static string multi_class_model_path;
	private static string dict_path;
	private static string one_class_model_path;

	private float thres_delta = 0.01f;

	enum RECOG_STATUS{
		FINISHED,
		PROCESSING
	}

	private static RECOG_STATUS _recognition_finished;

	public class ImagePixels
	{
		public int width;
		public int height;
		public byte[] pixels;
		public ImagePixels (int w, int h, byte[] p) {
			width = w;
			height = h;
			pixels = p;
		}
	}

	void Start () {
		VuforiaBehaviour.Instance.RegisterVuforiaStartedCallback(OnVuforiaStarted);
		VuforiaBehaviour.Instance.RegisterOnPauseCallback(OnPause);
		VuforiaBehaviour.Instance.RegisterTrackablesUpdatedCallback(OnTrackablesUpdated);
		if (mutex == null) {
			mutex = new Mutex(false);
		}
		setRecognitionStatus (RECOG_STATUS.FINISHED);
		country_code = -1;

		text = GameObject.FindWithTag ("DebugLog").GetComponent<UnityEngine.UI.Text>();
		audio = GameObject.Find("Audios").GetComponent<Audio> ();
		model_display = GameObject.Find ("ModelDisplayControl").GetComponent<ModelDisplay> ();

		path = Application.streamingAssetsPath+"/";
		multi_class_model_path = path+"multi_class.model";
		dict_path = path+"dictionary.mat";
		one_class_model_path = path+"one_class.model";


		sw = new Stopwatch();
	}
		
	private void OnVuforiaStarted()
	{
		// Try register camera image format
		if (CameraDevice.Instance.SetFrameFormat(mPixelFormat, true))
		{
			UnityEngine.Debug.Log("Successfully registered pixel format " + mPixelFormat.ToString());
			mFormatRegistered = true;
		}
		else
		{
			UnityEngine.Debug.LogError("Failed to register pixel format " + mPixelFormat.ToString() +
				"\n the format may be unsupported by your device;" +
				"\n consider using a different pixel format.");
			mFormatRegistered = false;
		}
	}
		
	private void OnPause(bool paused)
	{
		if (paused)
		{
			UnityEngine.Debug.Log("App was paused");
			UnregisterFormat();
		}
		else
		{
			UnityEngine.Debug.Log("App was resumed");
			RegisterFormat();
		}
	}

	private static void setRecognitionStatus(RECOG_STATUS status)
	{
		mutex.WaitOne ();
		_recognition_finished = status;
		mutex.ReleaseMutex ();
	}

	private static bool recognition_finished()
	{
		return _recognition_finished == RECOG_STATUS.FINISHED;
	}
		
	private void OnTrackablesUpdated()
	{
		delta += Time.deltaTime;
		if (mFormatRegistered && delta > thres_delta)
		{
			if (mAccessCameraImage)
			{
				Vuforia.Image image = CameraDevice.Instance.GetCameraImage(mPixelFormat);

				if (image != null )
				{
					byte[] pixels = image.Pixels;
					if (pixels != null && pixels.Length > 0)
					{
						if(recognition_finished())
						{
							RecognitionSmoother.enqueue (country_code);
							var code = RecognitionSmoother.most_common ();
							if (country_code != code)
								text.text = "正在识别中...";
							else
								text.text = CountryMap.countries [code.ToString ()];
							if(audio.get_source()!=code.ToString ())
								audio.set_source (code.ToString ());
							if (model_display.get_source () != code)
								model_display.set_source (code);
							setRecognitionStatus (RECOG_STATUS.PROCESSING);
							UploadBytes (ref pixels, image.BufferWidth, image.BufferHeight);
						}
					}
				}
			}
			delta = 0f;
		}
	}

	void CountryRecognition(System.Object obj)
	{
		ImagePixels ip = (ImagePixels)obj;

		#if UNITY_IPHONE && !UNITY_EDITOR
		sw.Start ();
		country_code = predict (ip.pixels, ip.height, ip.width, 400, 200, 200, multi_class_model_path, one_class_model_path, dict_path, 0.4, ref prob);
		sw.Stop ();
		//UnityEngine.Debug.Log ("Recognition cost: "+sw.ElapsedMilliseconds+" ms\n");
		#else
		country_code = 1;
		#endif

		sw.Reset ();
		setRecognitionStatus (RECOG_STATUS.FINISHED);
	}

	void UploadBytes(ref byte[] pixels, int width, int height)
	{
		ImagePixels ip = new ImagePixels(width, height, pixels);
		ParameterizedThreadStart ts = new ParameterizedThreadStart(CountryRecognition);
		Thread thread = new Thread(ts);
		thread.Start(ip);
	}
		
	private void UnregisterFormat()
	{
		UnityEngine.Debug.Log("Unregistering camera pixel format " + mPixelFormat.ToString());
		CameraDevice.Instance.SetFrameFormat(mPixelFormat, false);
		mFormatRegistered = false;
	}

	private void RegisterFormat()
	{
		if (CameraDevice.Instance.SetFrameFormat(mPixelFormat, true))
		{
			UnityEngine.Debug.Log("Successfully registered camera pixel format " + mPixelFormat.ToString());
			mFormatRegistered = true;
		}
		else
		{
			UnityEngine.Debug.LogError("Failed to register camera pixel format " + mPixelFormat.ToString());
			mFormatRegistered = false;
		}
	}

	void Update () {
	
	}
}
