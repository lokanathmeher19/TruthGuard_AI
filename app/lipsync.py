import cv2
import numpy as np
import librosa
import os
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt

# Ensure annotation directory exists
ANNOTATED_DIR = "static/annotated"
os.makedirs(ANNOTATED_DIR, exist_ok=True)

def detect_lipsync_mismatch(video_path: str, max_duration: int = 15):
    """
    Analyzes the correlation between video motion energy and audio energy.
    Since MediaPipe is unavailable on this environment, we use frame differencing
    to estimate visual speech activity.
    
    Returns: (score, correlation, graph_path)
    """
    # 1. Extract Audio
    try:
        y, sr = librosa.load(video_path, duration=max_duration)
        if len(y) == 0:
            return 0.5, 0.0, None
    except:
        return 0.5, 0.0, None

    # 2. Extract Visual Motion Energy
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.5, 0.0, None
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0: fps = 30
    
    prev_gray = None
    motion_energy = []
    frame_count = 0
    max_frames = int(max_duration * fps)
    
    while True:
        ret, frame = cap.read()
        if not ret or frame_count >= max_frames:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Resize to small dimension for speed and to focus on macro movement (lips/jaw)
        small_gray = cv2.resize(gray, (64, 64))
        
        if prev_gray is not None:
            # Simple absolute difference
            diff = cv2.absdiff(small_gray, prev_gray)
            score = np.sum(diff)
            motion_energy.append(score)
        else:
            motion_energy.append(0)
            
        prev_gray = small_gray
        frame_count += 1
        
    cap.release()
    
    if len(motion_energy) < 10:
        return 0.5, 0.0, None
        
    # 3. Synchronize Signal Lengths
    # Calculate Audio RMS envelope to match video frame rate
    hop_length = int(sr / fps)
    # Ensure hop_length is valid (>=1)
    if hop_length < 1: hop_length = 512
    
    rms = librosa.feature.rms(y=y, frame_length=hop_length*2, hop_length=hop_length)[0]
    
    # Resample RMS to match motion_energy length exactly if close
    # Or just truncate both to min length
    min_len = min(len(motion_energy), len(rms))
    
    if min_len < 2:
        return 0.5, 0.0, None
        
    # Standardize (Z-Score) for comparison
    def z_norm(v):
        std = np.std(v)
        if std == 0: return v
        return (v - np.mean(v)) / std

    v_sig = z_norm(np.array(motion_energy[:min_len]))
    a_sig = z_norm(rms[:min_len])
    
    # 4. Correlation
    correlation = np.corrcoef(v_sig, a_sig)[0, 1]
    if np.isnan(correlation): correlation = 0.0
    
    # --- Generate Graph ---
    graph_path = None
    try:
        plt.figure(figsize=(10, 4))
        plt.plot(v_sig, label="Visual Mouth Movement", color='blue', alpha=0.7)
        plt.plot(a_sig, label="Audio Energy", color='orange', alpha=0.7)
        plt.title(f"Audio-Visual Synchronization (Correlation: {correlation:.2f})")
        plt.xlabel("Frame Index")
        plt.ylabel("Normalized Energy")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        base_name = os.path.basename(video_path)
        filename = f"lipsync_graph_{os.path.splitext(base_name)[0]}.png"
        save_path = os.path.join(ANNOTATED_DIR, filename)
        
        plt.savefig(save_path)
        plt.close()
        
        graph_path = f"/static/annotated/{filename}"
        
    except Exception as e:
        print(f"Graph generation failed: {e}")
        plt.close()

    # 5. Scoring
    if correlation > 0.25:
        score = 0.2
    elif correlation > 0.1:
        score = 0.5
    else:
        score = 0.8
        
    return score, correlation, graph_path
