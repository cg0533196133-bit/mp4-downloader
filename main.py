from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import requests
import os
from uuid import uuid4

app = FastAPI(title="MP4 Downloader", description="Downloader proxy for MP4 files - temporary storage only")

# תיקייה זמנית - ב-Render Free Tier הכול נמחק כשהאפליקציה ישנה (~15 דק')
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# חשוב: זה מאפשר גישה ישירה לקבצים דרך /files/...
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/download")
async def download_video(url: str):
    """
    מקבל URL של MP4, מוריד אותו לשרת (זמני), ומחזיר קישור חדש להורדה.
    דוגמה: /download?url=https://example.com/video.mp4
    """
    if not url.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="ה-URL חייב להסתיים ב-.mp4")

    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        response = requests.get(url, stream=True, timeout=60)  # 60 שניות timeout
        response.raise_for_status()  # זורק שגיאה אם לא 200
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בהורדה: {str(e)}")

    # כותב את הקובץ
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # הכתובת המלאה לקובץ (Render יוסיף את הדומיין האוטומטי)
    new_url = f"/files/{file_name}"

    return {
        "original_url": url,
        "new_url": new_url,
        "full_url": f"https://mp4-downloader-zxeu.onrender.com{new_url}",
        "note": "הקובץ זמני בלבד! הורד אותו מיד - הוא נמחק כשהאפליקציה ישנה (כ-15 דק' ללא שימוש)"
    }

@app.get("/")
async def root():
    return {
        "message": "ברוכים הבאים ל-MP4 Downloader!",
        "usage": "שלח GET ל /download?url=<כתובת_של_MP4>",
        "docs": "/docs (Swagger UI)"
    }
