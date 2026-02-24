# Project Report: TruthGuard - Deepfake Detection System

## 1. Executive Summary
**TruthGuard** is a multi-modal forensic system designed to detect synthetic media (deepfakes) across image, video, and audio formats. In response to Problem Statement 02, this system analyzes files for manipulated facial expressions, lip-sync mismatches, synthetic voice patterns, and metadata anomalies to provide a confidence score and explainable verdict in near real-time.

---

## 2. System Architecture & Methodology

The system follows a modular architecture where uploaded content is routed to specific analysis engines based on file type. The results are then fused to generate a final probability score.

### 2.1 Video Analysis Module
The video engine performs a two-stage analysis: by-passing the need for heavy GPU resources by using efficient computer vision heuristics.

*   **Facial Consistency Analysis**:
    *   **Method**: Uses **OpenCV Haar Cascades** to detect faces and eyes frame-by-frame.
    *   **Logic**: Tracks the stability of face detection over time. Deepfakes often exhibit "flickering" or loss of face detection in individual frames. It also monitors eye detection to identify unnatural blinking patterns (e.g., lack of blinking or static eyes).
*   **Lip-Sync Verification**:
    *   **Method**: **Audio-Visual Correlation**.
    *   **Logic**: Extracts the amplitude envelope of the audio and correlates it with the "visual motion energy" of the face region (calculated via frame differencing).
    *   **Detection**: A low correlation coefficient (< 0.2) indicates that lip movements do not match the speech (dubbing or face swap).

### 2.2 Audio Analysis Module
Designed to detect text-to-speech (TTS) and voice cloning.

*   **Spectral Feature Extraction**: Uses **Librosa** to calculate MFCCs (Mel-frequency cepstral coefficients) and Spectral Flatness.
    *   **Synthetic Signature**: AI voices often exhibit unnaturally high spectral flatness (too clean) or lack the complex micro-variations of human vocal cords.
*   **Pitch Stability**: Analyzes the variance of the fundamental frequency (F0). Robotic or low-quality clones often have unnaturally stable pitch or limited dynamic range.

### 2.3 Image Forensics Module
Identifies generation artifacts in static images.

*   **Laplacian Variance**: Measures image "blurriness". AI-generated faces (GANs) often have different texture statistics compared to real camera sensor noise.
*   **Fourier Transform (FFT)**: Analyzes the frequency domain to detect "checkerboard" artifacts common in Convolutional Neural Networks (CNNs) used for upscaling or generation.

### 2.4 Metadata & Digital Forensics
*   **EXIF Analysis**: Extracts file metadata to look for editing software signatures (e.g., "Photoshop", "Adobe Premiere") or the absence of camera creation data.

---

## 3. Decision Fusion Logic

The final confidence score ($S_{final}$) is a weighted average of individual component scores:

$$ S_{final} = w_1 \cdot S_{visual} + w_2 \cdot S_{audio} + w_3 \cdot S_{lipsync} + w_4 \cdot S_{metadata} $$

Where weights are dynamically adjusted based on available data (e.g., if a video has no audio, $w_{audio}$ and $w_{lipsync}$ become 0, and other weights increase).

---

## 4. Evaluation Metrics

To validate the system (Prototype Phase), the following metrics are used:

1.  **Accuracy (Proposed)**: % of correctly classified samples in a balanced dataset of Real vs. Fake media.
2.  **Inference Speed**: Time taken to process a 10-second clip. Target: < 15 seconds on CPU.
3.  **False Positive Rate (FPR)**: Crucial for avoiding flagging authentic user content as fake.
4.  **Correlation Coefficient (r)**: For Lip-Sync, we measure the Pearson correlation between audio and visual signals. Valid thresholds are $r > 0.3$ for Real and $r < 0.1$ for Fake.

---

## 5. Limitations & Improvement Roadmap

### Current Limitations
1.  **Heuristic Dependence**: The current prototype relies on signal processing heuristics (CV/DSP) rather than Deep Learning transformations. While fast and explainable, it may miss high-end "Hollywood-quality" deepfakes that simulate sensor noise perfectly.
2.  **Face Alignment**: Without MediaPipe (due to environment restrictions), face tracking is less robust to extreme head poses.

### Improvement Roadmap
*   **Phase 1 (Immediate)**: Integrate **ONNX Runtime** to run quantized Deep Learning models (e.g., XceptionNet) for frame-by-frame deepfake classification on CPU.
*   **Phase 2**: Implement **wav2lip** based training for a more advanced lip-sync discriminator.
*   **Phase 3**: Deploy a **Transformer-based** audio classifier to better detect high-quality voice clones (e.g., ElevenLabs).

---

## 6. Real-World Application
This system is deployed as a FastAPI web application, demonstrating:
*   **Drag-and-Drop Interface**: For ease of use.
*   **Granular Reporting**: Users see *why* a file was flagged (e.g., "Lip-Sync Mismatch" vs "Synthetic Audio").
*   **Scalability**: The modular code structure allows individual analysis engines to be upgraded without breaking the system.
