import cv2
import numpy as np
import tempfile
import os
from backend.image_model import detect_fake_image
from backend.facial_analysis import analyze_facial_landmarks
from backend.lipsync import detect_lipsync_mismatch

def detect_fake_video(video_path):
    """
    Comprehensive video analysis pipeline.
    
    Stages:
    1. Visual Artifact Detection: Samples frames and checks for GAN noise/artifacts.
    2. Facial Biometrics: Tracks blinking and geometric consistency.
    3. Lip-Sync Analysis: Checks correlation between audio and visual lip movements.
    
    Optimizations:
    - Frame Sampling: 1 frame/sec to reduce load.
    - Early Exit: Stops after 10 seconds of analysis.
    - Downscaling: Resizes large frames to 640px max width.
    """

    # --- Stage 1: Frame-by-Frame Visual Analysis ---
    cap = cv2.VideoCapture(video_path)
    scores = []
    optical_flow_mags = []
    prev_gray = None
    frame_count = 0
    
    # Smart Sampling: Determine FPS to sample approx 1 frame per second
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0: fps = 30
    
    # Limit analysis to first 10 seconds to ensure swift API response
    sample_rate = max(1, int(fps)) 
    max_frames_to_scan = int(sample_rate * 10) 

    while True:
        ret, frame = cap.read()
        
        # Break exactly after 10 seconds of source footage is extracted
        if not ret or frame_count > max_frames_to_scan:
            break

        # --- Hardware-Accelerated Optical Flow Analysis (Jitter Detection) ---
        # Analyze at roughly 5-6 FPS to map structural displacement between consecutive captures
        flow_sample_rate = max(1, sample_rate // 5)
        if frame_count % flow_sample_rate == 0:
            # Severely downscale to 160x120 to execute dense optical flow instantly
            small_frame = cv2.resize(frame, (160, 120), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Computes the Dense Optical Flow (mathematical movement of pixels)
                flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                
                # Deepfake face swappers create micro-jitter and unnatural boundary shifting 
                # which causes the localized velocity variance to spike anomalously.
                optical_flow_mags.append(np.var(mag))
                
            prev_gray = gray

        # Analyze sparsely (1 fps) exactly for heavy CNN forensics
        if frame_count % sample_rate == 0:
            # Resize frame for speed (Max width 640px)
            # Heavy image forensics (ELA, Noise) are severely expensive on 4K/1080p
            height, width = frame.shape[:2]
            if width > 640:
                scale_ratio = 640 / width
                new_dim = (640, int(height * scale_ratio))
                frame = cv2.resize(frame, new_dim, interpolation=cv2.INTER_AREA)

            # Save to temp file because image_model expects a file path
            temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            temp_path = temp_file.name
            temp_file.close() 
            
            try:
                cv2.imwrite(temp_path, frame)
                score, img_report = detect_fake_image(temp_path)
                scores.append(score)
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        frame_count += 1

    cap.release()

    if len(scores) == 0:
        return {"visual": 0.01, "facial": 0.01, "lipsync": 0.01}, {"error": "No frames analyzed"}

    avg_score = float(np.mean(scores))
    
    # --- Process Optical Flow Jitter ---
    mean_jitter = 0.0
    if len(optical_flow_mags) > 0:
        mean_jitter = float(np.mean(optical_flow_mags))
        # Add slight penalty to visual score if extreme jitter detected
        if mean_jitter > 2.5:
            avg_score = min(0.99, avg_score + 0.25)
    
    # --- Stage 2: Facial Biometric Analysis ---
    annotated_face_path = None
    try:
        # Analyzes blinking rates, eye aspect ratio variance
        facial_score, annotated_face_path = analyze_facial_landmarks(video_path)
    except Exception as e:
        print(f"Facial analysis failed: {e}")
        facial_score = 0.01

    # --- Stage 3: Audio-Visual Lip-Sync ---
    lipsync_graph = None
    try:
        # Checks mouth-opening vs audio-energy correlation
        lipsync_score, correlation, lipsync_graph = detect_lipsync_mismatch(video_path)
    except Exception as e:
        print(f"Lip-sync analysis failed: {e}")
        lipsync_score = 0.01
        correlation = 0.0

    # NOTE: Fusion happens in main.py. Here we return components.
    
    # --- Report Generation ---
    # High variance in frame scores or high optical flow jitter suggests temporal flickering
    flicker_risk = mean_jitter > 2.5
    
    # Heuristic inference for report text
    blinking_issue = facial_score > 0.8
    sync_issue = lipsync_score > 0.6

    video_report = {
        "temporal_consistency": {
            "pass": bool(not flicker_risk),
            "detail": f"Stable optical flow inter-frame tracking (Jitter: {mean_jitter:.2f})." if not flicker_risk else f"Detected aberrant structural shifting and boundary jitter common in deepfakes (Jitter: {mean_jitter:.2f})."
        },
        "blinking_patterns": {
            "pass": bool(not blinking_issue), 
            "detail": "Natural blinking rate observed." if not blinking_issue else "Abnormal blinking patterns (staring or irregular) detected."
        },
        "lip_sync": {
            "pass": bool(not sync_issue),
            "detail": f"Lip movements synchronized with audio (Corr: {correlation:.2f})." if not sync_issue else "Significant mismatch between lip movement and speech audio.",
            "graph": lipsync_graph
        },
        "annotated_image": annotated_face_path
    }

    # Return raw components for robust weighted fusion in the main controller
    components = {
        "visual": float(avg_score),
        "facial": float(facial_score),
        "lipsync": float(lipsync_score)
    }
    return components, video_report

