import cv2
import numpy as np
import traceback

def analyze_steganography(image_path):
    """
    Advanced Forensic Steganography Detection.
    Attempts to detect hidden payloads (Like C2 instructions, illegal material,
    or encoded malware) injected into the Least Significant Bits (LSB) of the image pixels.
    """
    try:
        # Load image in grayscale to analyze pure intensity values
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
             return {"error": "Failed to load image for steganography analysis"}
             
        # Extract the Least Significant Bit (LSB) plane
        # Real images have natural noise in the LSB plane.
        # Steganography forces the LSB plane to hold deterministic encrypted data,
        # which looks like pure white noise / mathematically uniform distribution.
        lsb_plane = img & 1 
        
        # Calculate the mathematical variance of the LSB plane
        variance = np.var(lsb_plane)
        
        # Calculate the mean (average value) of the LSB plane
        mean = np.mean(lsb_plane)
        
        # Calculate standard deviation
        std_dev = np.std(lsb_plane)
        
        # If the image was purely random (like encrypted data), 
        # the mean would be exactly 0.5 and the variance would be exactly 0.25
        # We look for deviations that are *too perfect*
        
        is_suspicious = False
        risk_level = "LOW"
        details = "Normal pixel noise distribution detected."
        
        # Thresholds indicating high probability of embedded deterministic data
        # Note: Extremely "perfect" variance around 0.25 (e.g., 0.249 to 0.251) indicates 
        # that the LSB is functioning as a data carrier rather than natural camera sensor noise.
        if 0.248 < variance < 0.252 and 0.495 < mean < 0.505:
            is_suspicious = True
            risk_level = "CRITICAL"
            details = "Anomalous uniform noise detected in LSB plane. High probability of encrypted steganographic payload."
        
        # Generate a visual heatmap of the LSB plane for the user to see the hidden data
        # Scale the 0 and 1 values to 0 and 255 for a visible image
        lsb_visual = lsb_plane * 255
        
        # Apply a colormap to make the steganography "pop"
        # We convert back to BGR just to apply the heatmap
        lsb_color = cv2.cvtColor(lsb_visual.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        heatmap = cv2.applyColorMap(lsb_color, cv2.COLORMAP_JET)
        
        output_data = {
            "lsb_variance": float(variance),
            "lsb_mean": float(mean),
            "lsb_std_dev": float(std_dev),
            "steganography_detected": is_suspicious,
            "risk_level": risk_level,
            "analysis": details,
        }
        
        return output_data
        
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Steganography analysis crashed: {str(e)}"}
