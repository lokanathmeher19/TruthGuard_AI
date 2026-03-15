import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Handle cloud-native temporary storage (Vercel uses /tmp)
IS_VERCEL = os.environ.get("VERCEL") == "1"

if IS_VERCEL:
    UPLOAD_DIR = "/tmp/uploads"
    # On Vercel, we can't write to the frontend directory.
    # We'll save all generated assets to UPLOAD_DIR.
    STATIC_DIR = "/tmp/static"
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    STATIC_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'truthguard.db')}")
