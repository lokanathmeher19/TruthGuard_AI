import cv2
import numpy as np
import os
import torch
from app.image_model import AI_VISION_MODULE

# Load the pre-trained Haar Cascade classifier for Face Locating
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

ANNOTATED_DIR = "static/annotated"
os.makedirs(ANNOTATED_DIR, exist_ok=True)

def analyze_facial_landmarks(video_path: str, max_duration: int = 10):
    """
    Analyzes faces inside a video. 
    UPGRADE: Instead of basic flickering heuristics, this now extracts 
    the bounding box of the face and passes the actual face crop into 
    the PyTorch ResNet-50 deep learning model!
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.01, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0: fps = 30
    
    frame_interval = int(fps / 2) # Process 2 frames per second
    
    frame_count = 0
    faces_found = 0
    deep_learning_scores = []
    
    annotated_image_path = None
    saved_annotation = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count / fps > max_duration:
            break
            
        if frame_count % frame_interval != 0:
            frame_count += 1
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Locate Face
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            faces_found += 1
            (x, y, w, h) = faces[0]
            
            # --- Draw Bounding Box (AI Target Box) ---
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 229, 255), 2)
            cv2.putText(frame, "PyTorch Target", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255), 2)
            
            # --- 2. DEEP LEARNING FACIAL CROP ANALYSIS ---
            # Crop the face out and analyze it using the PyTorch ResNet Model
            face_crop = frame[y:y+h, x:x+w]
            
            # We temporarily save the face crop to disk so PyTorch PIL loader can grab it 
            # (or we could pass the array, but image_model expects a path)
            temp_crop_path = os.path.join(ANNOTATED_DIR, "temp_face_crop.jpg")
            cv2.imwrite(temp_crop_path, face_crop)
            
            # Run Deep Learning
            ai_score, ai_report = AI_VISION_MODULE.predict(temp_crop_path)
            deep_learning_scores.append(ai_score)
            
            # Eyes overlay for visualization
            eyes = eye_cascade.detectMultiScale(gray[y:y+h, x:x+w])
            for (ex, ey, ew, eh) in eyes:
                center = (x + ex + ew//2, y + ey + eh//2)
                radius = int((ew + eh) * 0.25)
                cv2.circle(frame, center, radius, (122, 92, 255), 2)
            
            # Save the annotated frame for the web UI
            if not saved_annotation:
                base_name = os.path.basename(video_path)
                filename = f"annotated_{os.path.splitext(base_name)[0]}.jpg"
                save_path = os.path.join(ANNOTATED_DIR, filename)
                cv2.imwrite(save_path, frame)
                
                annotated_image_path = f"/static/annotated/{filename}"
                saved_annotation = True
                
        frame_count += 1
        
    cap.release()
    
    if faces_found == 0 or len(deep_learning_scores) == 0:
        return 0.01, None
        
    # Aggregate PyTorch ResNet Scores across all analyzed video frames
    average_deepfake_probability = float(np.mean(deep_learning_scores))
    
    return average_deepfake_probability, annotated_image_path
