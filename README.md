# TruthGuard AI

**TruthGuard** is a multi-modal forensic system designed to detect synthetic media (deepfakes) across image, video, and audio formats. It analyzes files for manipulated facial expressions, lip-sync mismatches, synthetic voice patterns, and metadata anomalies to provide a confidence score and explainable verdict in near real-time.

## Features

### 🎬 Video Analysis
- **Facial Consistency Analysis**: Uses OpenCV Haar Cascades to detect faces and eyes frame-by-frame. Tracks the stability of face detection over time to identify "flickering" or unnatural blinking patterns often found in deepfakes.
- **Lip-Sync Verification**: Analyzes audio-visual correlation by extracting the amplitude envelope of the audio and correlating it with the "visual motion energy" of the face region to detect dubbing or face swaps.

### 🎙️ Audio Analysis
- **Spectral Feature Extraction**: Uses Librosa to calculate MFCCs (Mel-frequency cepstral coefficients) and Spectral Flatness to identify AI voices (TTS) and voice cloning by detecting unnaturally high spectral flatness or lack of complex micro-variations.
- **Pitch Stability Analysis**: Analyzes the variance of the fundamental frequency (F0) to spot robotic or low-quality clones with unnaturally stable pitch or limited dynamic range.

### 🖼️ Image Forensics
- **Laplacian Variance**: Measures image "blurriness" to detect AI-generated faces (GANs) which often have different texture statistics compared to real camera sensor noise.
- **Fourier Transform (FFT)**: Analyzes the frequency domain to detect "checkerboard" artifacts common in Convolutional Neural Networks (CNNs) used for upscaling or generation.

### 🔍 Metadata & Digital Forensics
- **EXIF Analysis**: Extracts file metadata to look for editing software signatures (e.g., Photoshop, Premiere) or the absence of camera creation data.

### 💻 Web Application
- **Modular FastAPI Backend**: Fast and robust backend architecture routing content to specific analysis engines based on file type.
- **Drag-and-Drop Interface**: Easy-to-use frontend for uploading media files.
- **Granular Reporting**: Provides detailed explanations of why a file was flagged, offering explainable AI insights instead of just a binary result.
- **Decision Fusion Engine**: Combines individual component scores into a final probability score using dynamic weighting based on available data (e.g., if a video has no audio, weights adjust accordingly).

## Running the Project

1. Run the `run_truthguard.bat` script which will automatically install dependencies and start the server:
   ```cmd
   .\run_truthguard.bat
   ```

2. Alternatively, manually install and run:
   ```cmd
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. Open your browser and navigate to `http://127.0.0.1:8000` to access the drag-and-drop web interface.