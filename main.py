from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = FastAPI(title="MP4 Downloader with yt-dlp", description="Downloader proxy using yt-dlp - temporary storage only")

# תיקייה זמנית - ב-Render Free Tier הכול נמחק כשהאפליקציה ישנה (~15 דק')
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# מאפשר גישה ישירה לקבצים דרך /files/...
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/download")
async def download_video(url: str):
    """
    מקבל URL (ישיר googlevideo או YouTube), מוריד עם yt-dlp לשרת (זמני), ומחזיר קישור חדש.
    דוגמה: /download?url=https://rr1---sn-....googlevideo.com/videoplayback?...
    """
    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    # אופציות yt-dlp – מוריד את ה-best mp4 זמין, בלי מיזוג אם לא צריך
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # best mp4 אפשרי
        'outtmpl': file_path,               # שומר ישירות לשם הקובץ
        'quiet': True,                      # פחות לוגים (אפשר False ל-debug)
        'no_warnings': True,
        'continuedl': True,                 # ממשיך אם נקטע
        'retries': 10,                      # נסיונות חוזרים
        'fragment_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
        },
        # אם רוצה להגביל גודל/מהירות – אפשר להוסיף
        # 'max_filesize': 2000000000,  # דוגמה: מקס 2GB
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # yt-dlp יטפל בקישור הישיר או ביוטיוב

        # בודק אם הקובץ נוצר (ליתר ביטחון)
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise Exception("הקובץ לא נוצר או ריק")

    except Exception as e:
        # נקה אם נכשל חלקית
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"שגיאה בהורדה עם yt-dlp: {str(e)}")

    # הכתובת החדשה
    new_url = f"/files/{file_name}"
    full_url = f"https://mp4-downloader-zxeu.onrender.com{new_url}"  # שנה אם הדומיין שלך שונה!

    return {
        "original_url": url,
        "new_url": new_url,
        "full_url": full_url,
        "note": "הקובץ זמני! הורד מיד - נמחק כשהאפליקציה ישנה (~15 דק' ללא שימוש). yt-dlp משמש להורדה."
    }

@app.get("/")
async def root():
    return {
        "message": "ברוכים הבאים ל-MP4 Downloader (עם yt-dlp)!",
        "usage": "שלח GET ל /download?url=<כתובת_של_וידאו_ישירה>",
        "docs": "/docs (Swagger UI)"
    }
