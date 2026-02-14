# ⚠️ IMPORTANT: Render Deployment Note

## This is a Desktop Application

This Sign Language AI application uses **Tkinter** which is a desktop GUI framework. 
It **CANNOT** be deployed to Render or any web hosting service.

## Why It Won't Work on Render:

1. **Tkinter requires a display** - Render servers have no GUI
2. **Camera access** - Needs local webcam
3. **TTS (pyttsx3)** - Requires system audio
4. **Desktop-only** - Not a web application

## How to Use:

### Run Locally:
```bash
pip install -r requirements.txt
python main.py
```

## If You Want Web Deployment:

You would need to create a completely different web version using:
- Flask/FastAPI for backend
- HTML/CSS/JavaScript for frontend
- WebRTC for camera access
- Web Speech API for TTS

This would require rewriting the entire application.

## Recommended Approach:

**Keep it as a desktop application** - It works perfectly on:
- ✅ Windows
- ✅ macOS  
- ✅ Linux

Users can download and run it locally with full camera and audio support.
