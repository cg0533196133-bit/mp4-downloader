from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import requests
import os
from uuid import uuid4

app = FastAPI(title="MP4 Downloader", description="Downloader proxy for MP4 files - temporary storage only")

# תיקייה זמנית - ב-Render Free Tier הכול נמחק כשהאפליקציה ישנה (~15 דק')
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# מאפשר גישה ישירה לקבצים דרך /files/...
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/download")
async def download_video(url: str):
    """
    מקבל URL של וידאו (לרוב mp4), מוריד אותו לשרת (זמני), ומחזיר קישור חדש להורדה.
    דוגמה: /download?url=https://rr1---sn-....googlevideo.com/videoplayback?...
    """
    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    # Headers שמחקים דפדפן אמיתי – חשוב מאוד נגד חסימות של YouTube/Google
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
        "Accept-Encoding": "identity",           # מונע דחיסה שמפריעה להורדת stream
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com",
        "Connection": "keep-alive",
        "Range": "bytes=0-",                     # מבקש את כל התוכן
        "Sec-Fetch-Dest": "video",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    try:
        response = requests.get(
            url,
            stream=True,
            timeout=120,               # יותר זמן – וידאו ארוך יכול לקחת
            headers=headers,
            allow_redirects=True
        )
        response.raise_for_status()  # זורק אם לא 200-299
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            raise HTTPException(
                status_code=400,
                detail="403 Forbidden - YouTube/Google כנראה חוסם את כתובת ה-IP של השרת (Render). נסה להשתמש בפרוקסי, VPN או yt-dlp במקום."
            )
        raise HTTPException(status_code=400, detail=f"שגיאה בהורדה: {str(http_err)} - סטטוס: {response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בהורדה: {str(e)}")

    # כותב את הקובץ
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # הכתובת החדשה
    new_url = f"/files/{file_name}"
    full_url = f"https://mp4-downloader-zxeu.onrender.com{new_url}"  # שנה אם הדומיין שלך שונה

    return {
        "original_url": url,
        "new_url": new_url,
        "full_url": full_url,
        "note": "הקובץ זמני! הורד מיד - נמחק כשהאפליקציה ישנה (~15 דק' ללא שימוש)"
    }

@app.get("/")
async def root():
    return {
        "message": "ברוכים הבאים ל-MP4 Downloader!",
        "usage": "שלח GET ל /download?url=<כתובת_של_וידאו>",
        "docs": "/docs (Swagger UI)"
    }
