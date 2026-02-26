import cv2
import numpy as np
import librosa
import mediapipe as mp
import matplotlib
import matplotlib.pyplot as plt
import os
import uuid
import tempfile
import warnings

# Use Agg backend for matplotlib to avoid UI threading errors globally
matplotlib.use('Agg')
warnings.filterwarnings("ignore")

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

def extract_audio_from_video(video_path, audio_path):
    """ Extracts the main audio track using MoviePy to avoid relying on direct FFmpeg shelling """
    import moviepy.editor as mp_ed
    try:
        vid = mp_ed.VideoFileClip(video_path)
        if vid.audio is None:
            return False
        vid.audio.write_audiofile(audio_path, verbose=False, logger=None)
        return os.path.exists(audio_path)
    except Exception as e:
        print(f"Moviepy Extraction Failed: {e}")
        return False

def detect_lipsync_mismatch(video_path):
    """
    Extracts mouth open distance and compares it chronologically with the acoustic energy 
    peaks of the synchronized audio track.
    Returns: lipsync_score (float 0.0-1.0), correlation (float), graph_url (str)
    """
    if not os.path.exists(MODEL_PATH):
        print("Model missing for Lipsync.")
        return 0.5, 0.0, None

    # Load media pipe
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    # Audio extraction
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, f"{uuid.uuid4().hex[:8]}.wav")
    
    has_audio = extract_audio_from_video(video_path, audio_path)
    if not has_audio:
        return 0.1, 0.0, None # Cannot cleanly check lipsync without audio

    # --- 1. Audio Energy RMS Extraction ---
    try:
        y, sr = librosa.load(audio_path, sr=16000)
    except Exception as e:
        if os.path.exists(audio_path): os.remove(audio_path)
        print(f"Librosa Read Error: {e}")
        return 0.1, 0.0, None
        
    hop_length = 512
    # Envelope extraction
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    if np.max(rms) > 0:
        rms = rms / np.max(rms)
        
    # --- 2. Visual Mouth Tracking ---
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0: fps = 30
    
    frame_interval = max(1, int(fps / 15))
    mouth_distances = []
    video_times = []
    
    frame_idx = 0
    max_frames = 150 # Check ~10s maximally
    
    while True:
        ret, frame = cap.read()
        if not ret or len(mouth_distances) >= max_frames:
            break
            
        if frame_idx % frame_interval == 0:
            height, width = frame.shape[:2]
            if width > 640:
                scale = 640 / width
                frame = cv2.resize(frame, (640, int(height * scale)), interpolation=cv2.INTER_AREA)
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection = detector.detect(mp_image)
            
            mouth_open = 0.0
            if len(detection.face_landmarks) > 0:
                lm = detection.face_landmarks[0]
                # Map lips. Nodes: Upper Lip Mid = 13, Lower Lip Mid = 14
                upper_lip = lm[13]
                lower_lip = lm[14]
                dist = abs(upper_lip.y - lower_lip.y)
                mouth_open = dist
                
            mouth_distances.append(mouth_open)
            video_times.append(frame_idx / fps)
            
        frame_idx += 1
        
    cap.release()
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except:
        pass
        
    if len(mouth_distances) < 10:
        return 0.1, 0.0, None
        
    mouth_distances = np.array(mouth_distances)
    if np.max(mouth_distances) > 0:
        mouth_distances = mouth_distances / np.max(mouth_distances)
        
    # --- 3. Time Series Correlation ---
    # Interpolate acoustic time steps over visual frames
    interp_audio_energy = np.interp(video_times, times, rms)
    
    if np.std(mouth_distances) == 0 or np.std(interp_audio_energy) == 0:
        corr = 0.0
    else:
        corr = np.corrcoef(mouth_distances, interp_audio_energy)[0, 1]
    
    if np.isnan(corr): corr = 0.0
    
    # --- 4. Graphical Artifact Generation ---
    plt.figure(figsize=(10, 4))
    plt.plot(video_times, mouth_distances, label='Mouth Opening Distance (Visual)', color='#0A84FF', linewidth=2)
    plt.plot(video_times, interp_audio_energy, label='Audio Energy Peak (Acoustic)', color='#FF3B30', alpha=0.7)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Normalized Magnitude')
    plt.title('Lip-Sync Correlational Analysis: Visual vs Acoustic')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = f"lipsync_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join("frontend", filename)
    os.makedirs("frontend", exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    
    graph_url = f"/frontend/{filename}"
    
    # --- 5. Detection Scoring ---
    # In Deepfakes (HeyGen, D-ID, Native face-swaps), generating a mouth exactly correlated to audio is hard.
    # We penalize low correlations mathematically.
    if corr < 0.15:
        lipsync_score = 0.92  # High mismatch chance -> Fake!
    elif corr < 0.35:
        lipsync_score = 0.70  # Suspicious -> Fake!
    else:
        lipsync_score = 0.10  # Authentic
        
    return lipsync_score, corr, graph_url
