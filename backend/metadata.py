import exifread
import os
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import cv2

def check_metadata(file_path):
    score = 0.0 # Start with low suspicion (Real)
    
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    try:
        created_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        created_time = "Unknown"
        
    file_format = os.path.splitext(file_path)[1].upper().replace(".", "")
    
    metadata_analysis = {
        "format": file_format,
        "file_size": f"{file_size_mb} MB",
        "resolution": "Unknown",
        "duration": "N/A",
        "software": "Unknown / Stripped",
        "device": "Unknown Device",
        "creation_date": created_time,
        "gps": "No Location Data",
        "risk_flags": [],
        "integrity_check": "Pass"
    }
    
    # Try to extract actual Media Capabilities
    try:
        if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if width > 0 and height > 0:
                    metadata_analysis["resolution"] = f"{width} x {height} px"
                if fps > 0 and frame_count > 0:
                    metadata_analysis["duration"] = f"{round(frame_count / fps, 2)} secs"
            cap.release()
        elif file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
            import librosa
            duration_sec = librosa.get_duration(path=file_path)
            metadata_analysis["duration"] = f"{round(duration_sec, 2)} secs"
        elif file_path.lower().endswith(('.jpg', '.png', '.jpeg')):
            with Image.open(file_path) as img:
                metadata_analysis["resolution"] = f"{img.width} x {img.height} px"
    except Exception as e:
        print("Media characteristic extraction error:", e)
    
    try:
        # A. Use ExifRead for detailed tag extraction
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # 1. Software / Platform Analysis
        software_tag = str(tags.get('Image Software', ''))
        metadata_analysis['software'] = software_tag if software_tag else "Unknown / Stripped"
        
        suspicious_keywords = [
            "Adobe", "Photoshop", "GIMP", "Edit", "Synthetic", "AI", "Generative", 
            "Stable Diffusion", "Midjourney", "DALL-E", "Canva", "InShot", "FaceApp"
        ]
        
        if software_tag:
            if any(keyword.lower() in software_tag.lower() for keyword in suspicious_keywords):
                score += 0.4
                metadata_analysis['software'] = f"{software_tag} (EDITING DETECTED)"
                metadata_analysis['risk_flags'].append(f"Editing Software Detected: {software_tag}")
        else:
            # Deep Binary Signature Scanning (If standard EXIF is stripped)
            # Many platforms strip EXIF but leave binary stamps in the atoms/headers.
            try:
                with open(file_path, 'rb') as bin_file:
                    f_size = os.path.getsize(file_path)
                    chunk_size = min(200000, f_size)
                    raw_bytes = bin_file.read(chunk_size)
                    if f_size > chunk_size:
                        bin_file.seek(-chunk_size, os.SEEK_END)
                        raw_bytes += bin_file.read()
                        
                    signatures = {
                        # Mainstream AI Chatbots & Consumer Platforms
                        b"ChatGPT": "ChatGPT (OpenAI Generator)", b"OpenAI": "ChatGPT / OpenAI (AI)",
                        b"Gemini": "Google Gemini (AI Generator)", b"SynthID": "Google DeepMind SynthID (Gemini Watermark)",
                        b"Copilot": "Microsoft Copilot (AI)", b"Claude": "Anthropic Claude (AI)",
                        b"Meta AI": "Meta AI Generator", b"DeepMind": "Google DeepMind (AI)",
                        
                        # AI Image Generators & Diffusion Models
                        b"Stable Diffusion": "Stable Diffusion (AI)", b"Midjourney": "Midjourney (AI)",
                        b"DALL": "DALL-E (ChatGPT Image AI)", b"Sora": "OpenAI Sora (Video AI)", b"ComfyUI": "ComfyUI / SD (AI)",
                        b"Automatic1111": "Automatic1111 (AI)", b"Fooocus": "Fooocus (AI)",
                        b"c2pa": "Content Credentials (C2PA AI Tag)", b"JUMBF": "JUMBF Meta (Likely AI)",
                        b"Leonardo": "Leonardo.ai (AI)", b"BingImageBuilder": "Microsoft Bing / Copilot (AI)",
                        b"Grok": "xAI Grok (AI)",
                        
                        # AI Video Generators
                        b"RunwayML": "RunwayML (AI)", b"Runway": "Runway Gen (AI)",
                        b"Pika": "Pika Labs (Video AI)", b"Luma": "Luma Dream Machine (Video AI)",
                        b"Kling": "Kling Video (AI)", b"HeyGen": "HeyGen Avatars (AI)",
                        b"Synthesia": "Synthesia (AI Avatars)",
                        
                        # AI Voice Cloners / TTS
                        b"ElevenLabs": "ElevenLabs (AI Voice)", b"PlayHT": "PlayHT (AI Voice)",
                        b"Suno": "Suno (AI Music/Audio)", b"Udio": "Udio (AI Audio)",
                        b"RVC": "Retrieval-based Voice Conversion (AI Voice)",
                        
                        # Professional & Mobile Editing Tools
                        b"Adobe": "Adobe Creative Cloud", b"Photoshop": "Adobe Photoshop",
                        b"Premiere": "Adobe Premiere", b"FaceApp": "FaceApp (Face Morph)",
                        b"Canva": "Canva App", b"InShot": "InShot Video Editor",
                        b"CapCut": "CapCut", b"Lightroom": "Adobe Lightroom",
                        
                        # Standard Original Cameras & Smartphones (REAL / AUTHENTIC Hardware)
                        b"Samsung": "Samsung Galaxy System", b"Pixel": "Google Pixel Smartphone",
                        b"Canon": "Canon EOS / DSLR", b"Nikon": "Nikon DSLR / Z-Series",
                        b"Sony": "Sony Alpha / Cinema Line", b"Panasonic": "Panasonic Lumix",
                        b"Fujifilm": "Fujifilm Digital Camera", b"GoPro": "GoPro Hero Camera",
                        b"DJI": "DJI Drone / Osmo", b"Hasselblad": "Hasselblad Camera",
                        b"Leica": "Leica Camera", b"Motorola": "Motorola Smartphone",
                        b"OnePlus": "OnePlus Smartphone", b"Xiaomi": "Xiaomi / Redmi System",
                        b"Vivo": "Vivo Smartphone", b"Oppo": "Oppo Smartphone", b"Realme": "Realme System",
                        b"Apple": "Apple / iOS", b"iPhone": "Apple iPhone", b"iPad": "Apple iPad",
                        b"Mac OS": "Apple Mac OS", b"Windows": "Windows OS",
                        b"Android": "Android System", b"Google": "Google Platform",
                        b"QuickTime": "Apple QuickTime Core",

                        # Standard Social & Messaging Platforms (Typically Real)
                        b"Lavf": "FFmpeg / Transcoder", b"FFmpeg": "FFmpeg / Transcoder",
                        b"WhatsApp": "WhatsApp", b"Instagram": "Instagram",
                        b"Snapchat": "Snapchat", b"Facebook": "Facebook",
                        b"TikTok": "TikTok", b"Telegram": "Telegram", b"Viber": "Viber",
                        b"Discord": "Discord", b"Twitter": "Twitter / X", b"Pinterest": "Pinterest"
                    }
                    
                    found_sig = False
                    for sig, platform_name in signatures.items():
                        if sig in raw_bytes:
                            metadata_analysis['software'] = f"{platform_name} (Deep Binary Scan)"
                            if "(AI" in platform_name or "FaceApp" in platform_name:
                                score += 0.9  # Direct AI signature is an immediate Critical Flag
                                metadata_analysis['risk_flags'].append(f"CRITICAL: {platform_name} Engine Signature Detected")
                            elif "Adobe" in platform_name:
                                score += 0.05
                                metadata_analysis['risk_flags'].append(f"Professional Editing Software Detected: {platform_name} (Not Inherently Malicious)")
                            found_sig = True
                            break
                            
                    if not found_sig:
                        # -----------------------------------------------------------------
                        # 🤖 AI HEURISTIC PLATFORM PREDICTION
                        # If the file is 100% stripped, we use ML-inspired heuristics
                        # based on compression, aspect ratio, and format to guess the source!
                        # -----------------------------------------------------------------
                        guessed_platform = "Unknown Source"
                        res = metadata_analysis.get('resolution', '')
                        fmt = metadata_analysis.get('format', '').upper()
                        size = file_size_mb
                        
                        if fmt in ['MP4', 'MOV']:
                            if '1080 x 1920' in res or '720 x 1280' in res:
                                guessed_platform = "TikTok / Reels (Mobile Vertical)"
                            elif '1920 x 1080' in res:
                                guessed_platform = "YouTube / DSLR (Standard HD)"
                            elif size < 16.0:  # WhatsApp video limit is normally 16MB
                                guessed_platform = "WhatsApp Video (Compressed)"
                        elif fmt in ['JPG', 'JPEG']:
                            if '1080 x 1350' in res or '1080 x 1080' in res:
                                guessed_platform = "Instagram Photo (Standard Square/Portrait)"
                            elif size < 0.5:
                                guessed_platform = "WhatsApp Deep-compressed Image"
                            else:
                                guessed_platform = "Web Download / Untracked"
                        elif fmt in ['PNG']:
                            if size > 1.0 and ('512 x 512' in res or '1024 x 1024' in res):
                                guessed_platform = "AI Generator (Midjourney/DALL-E)"
                                score += 0.85
                                metadata_analysis['risk_flags'].append("High Quality PNG with Diffusion Dimensions")
                            else:
                                guessed_platform = "Screen Capture / Web Graphic"
                        elif fmt in ['WAV', 'MP3']:
                            if size < 2.0:
                                guessed_platform = "Voice Note (WhatsApp/Telegram)"
                            else:
                                guessed_platform = "Studio / Podcast Recording"
                        
                        metadata_analysis['software'] = f"{guessed_platform} (Heuristic Prediction)"
            except Exception:
                metadata_analysis['software'] = "Unknown Source (Corrupted/Stripped)"

        # 2. Device Fingerprinting & Consistency
        make = str(tags.get('Image Make', ''))
        model = str(tags.get('Image Model', ''))
        
        if make or model:
            metadata_analysis['device'] = f"{make} {model}".strip()
            
            # Integrity Check: If camera make is present, we expect other camera details (Exposure, ISO)
            has_exposure = 'EXIF ExposureTime' in tags or 'EXIF ISOSpeedRatings' in tags
            if not has_exposure:
                metadata_analysis['risk_flags'].append("Incomplete Camera EXIF (Common in re-saves)")
                metadata_analysis['integrity_check'] = "Valid (Incomplete EXIF)"
        else:
            score += 0.0 
            metadata_analysis['risk_flags'].append("No Device Signature (Privacy Stripped or Generator)")

        # 3. Creation Date Security Check
        date_time = str(tags.get('EXIF DateTimeOriginal', ''))
        digitized_time = str(tags.get('EXIF DateTimeDigitized', ''))
        
        if date_time:
            metadata_analysis['creation_date'] = date_time
        
        # 4. Location / GPS Security
        if 'GPS GPSLatitude' in tags:
            metadata_analysis['gps'] = "Location Data Present (Authenticity Indicator)"
            score -= 0.15 # Strong signal of organic capture
        
        # 5. Pillow Analysis for Compression cues
        try:
            with Image.open(file_path) as img:
                if img.format == 'JPEG':
                    if not img.quantization:
                        metadata_analysis['risk_flags'].append("Suspicious Compression Pattern: Missing Quantization Tables (Non-standard JPEG)")
                        score += 0.20
                    elif len(img.quantization) < 2:
                        metadata_analysis['risk_flags'].append("Suspicious Compression Pattern: Unified Luma/Chroma Tables (AI Artifact)")
                        score += 0.15
                    
                    if 'adobe' in img.info:
                        score += 0.0
                        metadata_analysis['risk_flags'].append("Adobe Editing Software (Photoshop/Lightroom) Detected")
                        
                if img.format == 'PNG':
                   text_chunks = img.text
                   if 'parameters' in text_chunks or 'Software' in text_chunks.get('Software', ''):
                       if 'Stable Diffusion' in str(text_chunks) or 'Midjourney' in str(text_chunks):
                           score += 0.8
                           metadata_analysis['risk_flags'].append("AI Diffusion Metadata Found")
        except Exception:
            pass 

        # 6. Anomaly Detection
        if len(tags) < 3 and score < 0.2:
            metadata_analysis['risk_flags'].append("Missing camera metadata (Common in social media)")
            score = max(0.01, score - 0.05)
            
        metadata_score = min(max(score, 0.01), 0.99)
        return metadata_score, metadata_analysis

    except Exception as e:
        print(f"Metadata error: {e}")
        return 0.5, {"error": "Metadata extraction failed"}

