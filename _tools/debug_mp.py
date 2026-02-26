import sys
print(f"Python Ver: {sys.version}")

try:
    import google.protobuf
    print(f"Protobuf Ver: {google.protobuf.__version__}")
except ImportError as e:
    print(f"Protobuf Import Failed: {e}")

try:
    import mediapipe as mp
    print(f"MediaPipe Ver: {mp.__version__}")
    
    try:
        from mediapipe.python import solutions
        print("Explicit 'from mediapipe.python import solutions' worked!")
        mp.solutions = solutions
    except ImportError as e:
        print(f"Explicit Loading Failed: {e}")
        
    print(f"Has solutions? {hasattr(mp, 'solutions')}")
    if hasattr(mp, 'solutions'):
        print(f"Face Mesh: {mp.solutions.face_mesh}")

except ImportError as e:
    print(f"MediaPipe Import Failed: {e}")
