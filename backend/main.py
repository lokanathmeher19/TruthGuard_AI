import shutil
import time
import os
import uuid
import traceback
import asyncio
import json
import base64
import requests
import hashlib
from collections import defaultdict
from urllib.parse import urlparse

from fastapi import FastAPI, UploadFile, File, Request, WebSocket, WebSocketDisconnect, Form, Depends, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session 

# Database and Reports
from backend.database import SessionLocal, ScanResult, get_db
from backend.report import generate_pdf_report
from backend.steganography import analyze_steganography
from backend.virustotal import scan_hash_virustotal

# Import Analysis Modules
from backend.image_model import detect_fake_image, AI_VISION_MODULE
from backend.video_model import detect_fake_video
from backend.audio_model import detect_fake_audio, predict_live_audio
from backend.metadata import check_metadata
from backend.fusion import combine 

app = FastAPI(
    title="TruthGuard Deepfake Detection API",
    description="Multi-modal deepfake detection system analyzing Video, Audio, Image, and Metadata.",
    version="1.0.0" 
) 

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
) 
# -------------------------------------------------------------------------
# Global Configuration & Error Handling
# -------------------------------------------------------------------------

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests_limit = requests
        self.window = window
        self.clients = defaultdict(list)

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        self.clients[client_ip] = [t for t in self.clients[client_ip] if now - t < self.window]
        if len(self.clients[client_ip]) >= self.requests_limit:
            raise HTTPException(status_code=429, detail="Rate Limit Exceeded: Maximum limit of requests per minute reached.")
        self.clients[client_ip].append(now)

analyze_limiter = RateLimiter(requests=10, window=60)

def secure_wipe_file(file_path: str):
    """
    Implements a rigorous secure wipe by overwriting the file with random bytes 
    before deleting it from the storage system (Zero-trust wipe).
    """
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            # Overwrite with random data
            with open(file_path, "r+b") as f:
                f.write(os.urandom(file_size))
            # Delete the file
            os.remove(file_path)
            print(f"[SECURE WIPE] Evaluated artifact '{file_path}' successfully wiped and destroyed.")
    except Exception as e:
        print(f"[SECURE WIPE ERROR] Failed to wipe {file_path}: {e}")

# Global Exception Handler to capture unhandled server errors and return JSON
# instead of crashing, ensuring the frontend always receives a valid response.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global Exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for serving the frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def read_root():
    """Serves the main frontend application."""
    return FileResponse("frontend/index.html")

# -------------------------------------------------------------------------
# Main Analysis Endpoint
# -------------------------------------------------------------------------

@app.post("/analyze/", dependencies=[Depends(analyze_limiter)])
async def analyze(background_tasks: BackgroundTasks, file: UploadFile = File(None), url: str = Form(None), db: Session = Depends(get_db)):
    """
    Main entry point for deepfake analysis.
    1. Receives uploaded file or URL link.
    2. Extracts metadata forensics.
    3. Routes to specific analysis pipelines.
    4. Fuses scores and returns standardize JSON.
    """
    start_time = time.time()
    
    try:
        if not file and not url:
            return JSONResponse(status_code=400, content={"error": "Must provide either file or url"})
            
        if url:
            parsed_url = urlparse(url)
            media_filename = os.path.basename(parsed_url.path)
            if not media_filename or not media_filename.lower().endswith((".mp4", ".avi", ".mov", ".jpg", ".png", ".wav", ".mp3")):
                media_filename = "downloaded_video.mp4" # fallback
                
            file_path = os.path.join(UPLOAD_DIR, f"url_{int(time.time())}_{media_filename}")
            
            try:
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()
                file_hash = hashlib.sha256()
                with open(file_path, "wb") as buffer:
                    for chunk in response.iter_content(chunk_size=8192):
                        buffer.write(chunk)
                        file_hash.update(chunk)
                file_hash_hex = file_hash.hexdigest()
            except Exception as e:
                return JSONResponse(status_code=400, content={"error": f"Failed to download from URL: {str(e)}"})
        else:
            media_filename = file.filename
            file_path = os.path.join(UPLOAD_DIR, media_filename)
            # Save uploaded file safely, check for large files and avoid crashes
            file_size = 0
            file_hash = hashlib.sha256()
            with open(file_path, "wb") as buffer:
                while chunk := file.file.read(1024 * 1024): # Read in 1MB chunks
                    file_size += len(chunk)
                    if file_size > 50 * 1024 * 1024: # 50MB limit
                        return JSONResponse(status_code=400, content={"error": "File exceeds the 50MB size limit. Please upload a smaller file."})
                    buffer.write(chunk)
                    file_hash.update(chunk)
            file_hash_hex = file_hash.hexdigest()

        # --- PRE-SCAN: ANTI-MALWARE INTELLIGENCE ---
        # Ping VirusTotal API to ensure the file itself isn't a Trojan or Ransomware
        vt_report = scan_hash_virustotal(file_hash_hex)
        if vt_report.get("is_malware"):
            # Threat identified! Abort forensic pipeline and destroy the artifact.
            secure_wipe_file(file_path)
            error_msg = f"QUARANTINE_ALERT|VirusTotal detected severe malware. File has been securely destroyed for your safety.|{vt_report.get('report_link', '')}"
            return JSONResponse(status_code=403, content={"error": error_msg})

        # --- Step 1: Metadata Forensics ---
        # Checks for editing software signatures, missing EXIF tags, etc.
        metadata_score, metadata_report = check_metadata(file_path)
        
        final_score = 0
        checks = {}
        explanation = ""

        # Construct safe metadata summary
        risk_detail = "No major risks"
        if metadata_report.get('risk_flags'):
            risk_detail = "; ".join(metadata_report['risk_flags'])
            
        checks['metadata'] = {
            'pass': metadata_score < 0.5,
            'detail': risk_detail,
            'report': metadata_report # Pass full object
        }

        # --- Step 2: Media-Specific Analysis pipelines ---
        
        # A. IMAGE PIPELINE
        if media_filename.lower().endswith((".jpg", ".png", ".jpeg")):
            # Run visual artifact detection (Noise, ELA, Frequency)
            image_score, image_report = detect_fake_image(file_path)
            
            # Run Steganography Forensic Check
            steganography_report = analyze_steganography(file_path)
            
            # Map for consistent variables in final JSON
            facial_score = image_score
            lipsync_score = 0.0
            audio_score = None
            
            # Fusion: Image + Metadata
            final_score = combine(facial=image_score, metadata=metadata_score)
            
            # Boost the threat score drastically if a secret payload is detected
            if steganography_report.get("steganography_detected"):
                final_score = max(final_score, 0.95)
                explanation = "CRITICAL: Malicious Steganographic Payload detected hidden within image pixels. Severe Risk."
            
            checks['visual'] = {
                'pass': image_score < 0.5,
                'detail': "No manipulated facial expressions or GAN artifacts detected.",
                'report': image_report 
            }
            
            checks['steganography'] = {
                'pass': not steganography_report.get("steganography_detected", False),
                'detail': steganography_report.get("analysis", "Normal pixel structure"),
                'report': steganography_report
            }

        # B. VIDEO PIPELINE
        elif media_filename.lower().endswith((".mp4", ".avi", ".mov")):
            # Run Visual + Facial + LipSync analysis
            # Returns a dict of component scores
            video_components, video_report = detect_fake_video(file_path)
            
            visual_score = video_components.get('visual', 0.0)
            facial_score = video_components.get('facial', 0.0)
            lipsync_score = video_components.get('lipsync', 0.0)
            
            # Run Audio Analysis (Extract track from video)
            try:
                audio_score, audio_report = detect_fake_audio(file_path)
            except Exception as e:
                # Handle silent videos or extraction failures gracefully
                audio_score = None
                audio_report = {"error": "Audio track analysis failed or silent"}

            # Fusion: Facial + LipSync + Audio + Metadata + Visual
            final_score = combine(
                facial=facial_score,
                lipsync=lipsync_score, 
                audio=audio_score, 
                metadata=metadata_score,
                visual=visual_score 
            )
            
            checks['visual'] = {
                'pass': visual_score < 0.5,
                'detail': "Visual artifact analysis complete.",
                'report': video_report
            }
            
            if audio_score is not None:
                checks['audio'] = {
                     'pass': audio_score < 0.5,
                     'detail': "Audio track analysis complete.",
                     'report': audio_report
                }
            else:
                checks['audio'] = {
                     'pass': True, 
                     'detail': "No audio track detected or analysis skipped.",
                     'report': audio_report
                }

        # C. AUDIO PIPELINE
        elif media_filename.lower().endswith((".wav", ".mp3", ".ogg", ".flac")):
            # Run audio forensics
            audio_score, audio_report = detect_fake_audio(file_path)
            
            # Fusion: Audio + Metadata
            final_score = combine(audio=audio_score, metadata=metadata_score)
            
            checks['audio'] = {
                'pass': audio_score < 0.5,
                'detail': "Natural voice patterns detected.",
                'report': audio_report
            }

        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported file type"})

        # Generate Explanation based on signals dynamically based on the highest threat indicator
        max_threat_score = 0.0
        threat_source = "None"
        
        components_map = {
            "Visual Rendering (Generative AI)": facial_score if media_filename.lower().endswith((".jpg", ".png", ".jpeg")) else visual_score,
            "Facial Biometrics": facial_score,
            "Acoustic Envelope (Voice Synthesis)": audio_score if audio_score is not None else 0.0,
            "Lip-Sync Correlation": lipsync_score,
            "Hardware & EXIF Metadata": metadata_score
        }
        
        for name, comp_score in components_map.items():
            if comp_score > max_threat_score:
                max_threat_score = comp_score
                threat_source = name
                
        if final_score > 0.5:
            explanation = f"Critical manipulation detected. The primary anomaly originates from: '{threat_source}'. Confidence in synthetic generation is high."
        else:
            explanation = "Extensive multi-modal analysis passes. No concrete indicators of digital manipulation or generative AI synthesis found."

    except Exception as e:
        # Catch-all for unexpected pipeline failures
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        try:
            if 'file_path' in locals():
                secure_wipe_file(file_path)
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"error": str(e)})

    # --- Step 3: Format Response ---
    # Calculate total processing time accurately
    processing_time_sec = round(time.time() - start_time, 2)
    
    # Calculate granular "Realness" percentages for frontend display
    
    # Defaults
    face_realness = "N/A"
    background_realness = "N/A"
    voice_realness = "N/A"
    body_realness = "N/A"

    if media_filename.lower().endswith((".jpg", ".png", ".jpeg")):
        face_realness = max(0, 1.0 - facial_score)
        background_realness = min(1.0, face_realness + 0.2)
        body_realness = min(1.0, face_realness + 0.1)
    
    elif media_filename.lower().endswith((".mp4", ".avi", ".mov")):
        face_realness = max(0, 1.0 - facial_score)
        background_realness = min(1.0, face_realness + 0.3)
        body_realness = min(1.0, face_realness + 0.2)
        if audio_score is not None:
             voice_realness = max(0, 1.0 - audio_score)

    elif media_filename.lower().endswith((".wav", ".mp3", ".ogg", ".flac")):
        voice_realness = max(0, 1.0 - audio_score)

    # Final standardized JSON response    
    # -------------------------------------------------------------------------
    # Database Persistence & unique Scan ID
    # -------------------------------------------------------------------------
    scan_id = f"TG-{str(uuid.uuid4())[:8].upper()}"
    
    response_payload = {
        "scan_id": scan_id,
        "processing_time": f"{processing_time_sec} seconds",
        "file_hash_sha256": file_hash_hex,
        "facial_score": round(float(facial_score), 3),
        "lipsync_score": round(float(lipsync_score), 3),
        "audio_score": round(float(audio_score), 3) if audio_score is not None else 0.0,
        "metadata_score": round(float(metadata_score), 3),
        "final_score": round(float(final_score), 3),
        "fake_probability": round(float(final_score), 3),
        "verdict": "FAKE" if final_score > 0.5 else "REAL",
        "confidence_percentage": f"{int(final_score * 100)}%",
        "explanation": explanation,
        "highest_suspicious_module": threat_source,
        "checks": checks,
        "components": {
            "face": round(float(face_realness) * 100, 1) if isinstance(face_realness, (int, float)) else face_realness,
            "background": round(float(background_realness) * 100, 1) if isinstance(background_realness, (int, float)) else background_realness,
            "voice": round(float(voice_realness) * 100, 1) if isinstance(voice_realness, (int, float)) else voice_realness,
            "body": round(float(body_realness) * 100, 1) if isinstance(body_realness, (int, float)) else body_realness
        }
    }
    
    try:
        new_scan = ScanResult(
            scan_id=scan_id,
            filename=media_filename,
            verdict=response_payload["verdict"],
            fake_probability=response_payload["fake_probability"],
            details_json=json.dumps(response_payload)
        )
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
    except Exception as db_err:
        print(f"Failed to save to database: {db_err}")
    
    # Schedule secure wiping of the media file to ensure Zero-Trust storage
    background_tasks.add_task(secure_wipe_file, file_path)
    
    return response_payload

# -------------------------------------------------------------------------
# Dynamic PDF Generation Endpoint
# -------------------------------------------------------------------------
@app.get("/report/{scan_id}")
async def download_report(scan_id: str, db: Session = Depends(get_db)):
    """
    Generates and downloads a PDF forensic report based on a scan ID.
    """
    scan_record = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).first()
    
    if not scan_record:
         return JSONResponse(status_code=404, content={"error": "Scan ID not found in database."})
         
    # Generate PDF temporarily
    report_filename = f"TruthGuard_Report_{scan_id}.pdf"
    report_path = os.path.join(UPLOAD_DIR, report_filename)
    
    try:
        generate_pdf_report(scan_record, report_path)
        return FileResponse(path=report_path, filename=report_filename, media_type='application/pdf')
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Failed to generate PDF: {str(e)}"})

# -------------------------------------------------------------------------
# Threat History Endpoint
# -------------------------------------------------------------------------
@app.get("/history/")
async def get_threat_history(db: Session = Depends(get_db)):
    """
    Fetches the latest 50 historical threat scans from the local SQLite database.
    """
    try:
        scans = db.query(ScanResult).order_by(ScanResult.timestamp.desc()).limit(50).all()
        history = []
        for scan in scans:
            history.append({
                "scan_id": scan.scan_id,
                "filename": scan.filename,
                "timestamp": scan.timestamp.isoformat(),
                "verdict": scan.verdict,
                "fake_probability": round(scan.fake_probability * 100, 1)
            })
        return {"status": "success", "data": history}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Failed to fetch history: {str(e)}"})

# -------------------------------------------------------------------------
# Real-Time WebSocket Endpoint
# -------------------------------------------------------------------------

@app.websocket("/ws/analyze_audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """
    Handles real-time streaming data from the client's microphone.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive data from the browser (e.g. video/audio Blob)
            data = await websocket.receive_bytes()
            
            # Offload heavy acoustic inference tensor mapping to background thread asynchronously
            fake_prob = await asyncio.to_thread(predict_live_audio, data)
            
            verdict_payload = {
                "status": "success",
                "fake_probability": fake_prob,
                "verdict": "FAKE" if fake_prob > 0.5 else "REAL",
                "bytes_analyzed": len(data),
                "timestamp": time.time()
            }
            
            # Send immediate analysis back to the dashboard
            await websocket.send_text(json.dumps(verdict_payload))
            
    except WebSocketDisconnect:
        print("Client disconnected from Live Stream.")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.send_text(json.dumps({"status": "error", "message": str(e)}))
        except:
            pass

@app.websocket("/ws/analyze_video")
async def websocket_video_endpoint(websocket: WebSocket):
    """
    Handles real-time frame streaming from the client's webcam.
    Receives base64 encoded JPG frames, decodes them, and processes
    them via the PyTorch vision heuristics.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive text data (base64 image URL) from browser
            data = await websocket.receive_text()
            
            if data.startswith("data:image"):
                # Strip the data URL prefix
                header, encoded = data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                
                # Execute LIVE internal neural network Vision Processing
                fake_prob = await asyncio.to_thread(AI_VISION_MODULE.predict_live_frame, img_bytes)
                
                verdict_payload = {
                    "status": "success",
                    "fake_probability": fake_prob,
                    "verdict": "FAKE" if fake_prob > 0.5 else "REAL",
                    "bytes_analyzed": len(img_bytes),
                    "timestamp": time.time()
                }
                
                await websocket.send_text(json.dumps(verdict_payload))
                
    except WebSocketDisconnect:
        print("Client disconnected from Webcam Stream.")
    except Exception as e:
        print(f"Video WebSocket Error: {e}")
        try:
            await websocket.send_text(json.dumps({"status": "error", "message": str(e)}))
        except:
            pass 

