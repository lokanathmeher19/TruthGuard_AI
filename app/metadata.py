import exifread
import os
import datetime
from PIL import Image
from PIL.ExifTags import TAGS

def check_metadata(file_path):
    score = 0.0 # Start with low suspicion (Real)
    
    analysis_report = {
        "software": "Unknown / Stripped",
        "device": "Unknown Device",
        "creation_date": "Unknown",
        "gps": "No Location Data",
        "risk_flags": [],
        "integrity_check": "Pass"
    }
    
    try:
        # A. Use ExifRead for detailed tag extraction
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # 1. Software / Platform Analysis
        software_tag = str(tags.get('Image Software', ''))
        analysis_report['software'] = software_tag if software_tag else "Unknown / Stripped"
        
        suspicious_keywords = [
            "Adobe", "Photoshop", "GIMP", "Edit", "Synthetic", "AI", "Generative", 
            "Stable Diffusion", "Midjourney", "DALL-E", "Canva", "InShot", "FaceApp"
        ]
        
        if software_tag:
            if any(keyword.lower() in software_tag.lower() for keyword in suspicious_keywords):
                score += 0.4
                analysis_report['software'] = f"{software_tag} (EDITING DETECTED)"
                analysis_report['risk_flags'].append(f"Editing Software Detected: {software_tag}")
        else:
            # Missing software tag is common in untouched raw photos but also in stripped files.
            # We don't penalize heavily unless other things are wrong.
            pass

        # 2. Device Fingerprinting & Consistency
        make = str(tags.get('Image Make', ''))
        model = str(tags.get('Image Model', ''))
        
        if make or model:
            analysis_report['device'] = f"{make} {model}".strip()
            
            # Integrity Check: If camera make is present, we expect other camera details (Exposure, ISO)
            # If sophisticated tags are missing but Make is present, it's often a re-save that preserved partial EXIF.
            has_exposure = 'EXIF ExposureTime' in tags or 'EXIF ISOSpeedRatings' in tags
            if not has_exposure:
                score += 0.3
                analysis_report['risk_flags'].append("Incomplete Camera Metadata (Possible Re-save)")
                analysis_report['integrity_check'] = "Suspicious (Incomplete EXIF)"
        else:
            # No device info. Could be strict privacy setting OR generated image.
            # In deepfake context, totally stripped metadata is suspicious.
            score += 0.1 
            analysis_report['risk_flags'].append("No Device Signature Found")

        # 3. Creation Date Security Check
        date_time = str(tags.get('EXIF DateTimeOriginal', ''))
        digitized_time = str(tags.get('EXIF DateTimeDigitized', ''))
        
        if date_time:
            analysis_report['creation_date'] = date_time
            # Check for modification discrepancies if digitized time exists
            if digitized_time and date_time != digitized_time:
                 # Small diffs are okay, but usually they match for camera originals.
                 # This is a weak signal, so we just note it if needed, or ignore.
                 pass
        
        # 4. Location / GPS Security
        if 'GPS GPSLatitude' in tags:
            analysis_report['gps'] = "Location Data Present (Authenticity Indicator)"
            # GPS presence usually indicates a real photo (privacy risk mostly, but good for realness)
            score -= 0.1 
        
        # 5. Pillow Analysis for Quantization/Compression cues
        try:
            with Image.open(file_path) as img:
                # Check for quantization tables (JPEG)
                if img.format == 'JPEG':
                    if not img.quantization:
                        score += 0.2
                        analysis_report['risk_flags'].append("Missing Quantization Tables (Non-standard JPEG)")
                    
                    # Check for "Adobe" APP14 marker (common in Photoshop saves)
                    if 'adobe' in img.info:
                        score += 0.2
                        analysis_report['risk_flags'].append("Adobe Ducky/APP14 Marker Detected")
                        
                # Check for AI-generation metadata embedded in PNG chunks (e.g. "parameters" in Stable Diffusion)
                if img.format == 'PNG':
                   text_chunks = img.text
                   if 'parameters' in text_chunks or 'Software' in text_chunks.get('Software', ''):
                       if 'Stable Diffusion' in str(text_chunks):
                           score += 0.8
                           analysis_report['risk_flags'].append("Stable Diffusion Metadata Found")
        except Exception:
            pass # Pillow analysis is optional

        # 6. Anomaly Detection (Total Strip)
        if len(tags) < 3 and score < 0.2:
            # If practically no tags and no other flags, it's highly suspicious (stripped)
            score += 0.3
            analysis_report['risk_flags'].append("Deep Metadata Stripped (High Anonymity)")
            
        final_score = min(max(score, 0.0), 1.0)
        return final_score, analysis_report

    except Exception as e:
        print(f"Metadata error: {e}")
        return 0.5, {"error": "Metadata extraction failed"}

