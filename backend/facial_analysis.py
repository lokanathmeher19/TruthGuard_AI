import cv2
import numpy as np
import os
import uuid
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Set absolute path for the downloaded face landmarker model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

def analyze_facial_landmarks(video_path):
    """
    Extracts facial landmarks from video frames and calculates geometric changes
    over time to detect manipulation such as deepfakes.
    Returns facial_score (0-1) and the path to the annotated image.
    """
    if not os.path.exists(MODEL_PATH):
        # Graceful degradation if model missing
        print(f"Face landmarker model missing at {MODEL_PATH}")
        return 0.05, None 

    # Load FaceLandmarker Model
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)
    
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0: fps = 30
    
    max_frames = 150 
    frame_interval = max(1, int(fps / 15)) 
    
    frame_count = 0
    all_landmarks_across_frames = []
    
    saved_annotated = False
    annotated_face_url = None
    
    while True:
        ret, frame = cap.read()
        if not ret or len(all_landmarks_across_frames) >= max_frames:
            break
            
        if frame_count % frame_interval == 0:
            height, width = frame.shape[:2]
            if width > 640:
                scale_ratio = 640 / width
                frame = cv2.resize(frame, (640, int(height * scale_ratio)), interpolation=cv2.INTER_AREA)
            
            # Convert OpenCV frame BGR to MediaPipe Image expected format (RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Detect
            detection_result = detector.detect(mp_image)
            
            if len(detection_result.face_landmarks) > 0:
                # Get the first face detected
                face_lm = detection_result.face_landmarks[0]
                
                # Save annotated frame showing the geometry
                if not saved_annotated:
                    annotated_frame = frame.copy()
                    h, w = annotated_frame.shape[:2]
                    # Draw subtle green dot map to avoid huge file sizes or thick connections
                    for lm in face_lm:
                        x = int(lm.x * w)
                        y = int(lm.y * h)
                        cv2.circle(annotated_frame, (x, y), 1, (0, 255, 0), -1)
                        
                    filename = f"annotated_{uuid.uuid4().hex[:8]}.jpg"
                    save_path = os.path.join("frontend", filename)
                    os.makedirs("frontend", exist_ok=True)
                    cv2.imwrite(save_path, annotated_frame)
                    
                    annotated_face_url = f"/frontend/{filename}"
                    saved_annotated = True
                
                # Normalize and collect the facial landmark geometry representation 
                pts = np.array([[lm.x, lm.y, lm.z] for lm in face_lm])
                all_landmarks_across_frames.append(pts)
                
        frame_count += 1
        
    cap.release()
    
    if len(all_landmarks_across_frames) < 3:
        return 0.05, None # Insufficient data
        
    # Standard deviation analysis of coordinate variance over time (frames)
    # Allows us to track unnatural jitter or completely frozen geometry characteristic of deepfakes
    landmarks_tensor = np.array(all_landmarks_across_frames)
    nose_tip = landmarks_tensor[:, 1:2, :]
    centered = landmarks_tensor - nose_tip
    
    var_across_frames = np.var(centered, axis=0) # Shape: (478, 3)
    mean_variance = float(np.mean(var_across_frames))
    
    facial_score = 0.15 
    
    if mean_variance < 0.00005: 
        # Score highly as completely rigid frame-by-frame (freeze-style gen)
        facial_score = 0.88
    elif mean_variance > 0.005:
        # Score highly as completely jittery with high un-smoothed artifacts
        facial_score = 0.75
    else:
        # Penalize for slightly too rigid variance values
        rigid_factor = (0.0005 - mean_variance) * 1000
        if rigid_factor > 0:
            facial_score += min(0.6, rigid_factor)
            
    # clamp output percentage safely inside bounds [0.01 - 0.99]
    facial_score = max(0.01, min(0.99, facial_score))

    return facial_score, annotated_face_url 











