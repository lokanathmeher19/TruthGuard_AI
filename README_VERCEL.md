# Vercel Deployment Guide for TruthGuard AI

This project has been restructured for seamless deployment on Vercel.

## Structure Changes
- **`api/index.py`**: The main entry point for Vercel Serverless Functions. It imports the FastAPI app from `backend/main.py`.
- **`vercel.json`**: Configures the build and routing.
- **`backend/config.py`**: Manages environment variables and paths.
- **`requirements.txt`**: Updated with all necessary cloud dependencies.

## Deployment Steps
1. **Push to GitHub**: Upload your project to a GitHub repository.
2. **Connect to Vercel**: Import the project in the Vercel dashboard.
3. **Environment Variables**:
   - `DATABASE_URL`: (Optional) Connect a Postgres or other database. Defaults to local SQLite.
   - `VT_API_KEY`: (Optional) Your VirusTotal API Key.
4. **Deploy**: Vercel will automatically detect the configuration and deploy the frontend and backend.

## Technical Notes
- **Temporary Storage**: Vercel uses a read-only filesystem except for `/tmp`. The app is configured to use `/tmp/uploads` for processing.
- **Static Assets**: Generated forensic reports and graphs are saved to `/tmp` and served via the `/frontend/generated/` route.
- **WebSockets**: Note that Vercel Serverless Functions do not support persistent WebSockets. For production real-time features, consider a dedicated server or a service like Pusher/Ably, or use long-polling.
