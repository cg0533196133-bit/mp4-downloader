from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = FastAPI(title="MP4 Downloader with yt-dlp (Direct Links)", description="Supports direct googlevideo links + YouTube URLs")

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/download")
async def download_video(url: str):
    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    ydl_opts = {
        'format': 'best[ext=mp4]/best',     # עדיפות ל-mp4, fallback ל-best
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'continuedl': True,
        'retries': 10,
        'fragment_retries': 10,
        'noplaylist': True,
        'force_generic_extractor': True,    # ← המפתח לקישורים ישירים!
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Range': 'bytes=0-',
            'Connection': 'keep-alive',
        },
        'no_check_certificate': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:  # בדיקה אם קובץ ריק/HTML
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception("ההורדה נכשלה – נראה שהתקבל HTML במקום וידאו. הקישור פג תוקף או חסום.")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"שגיאה בהורדה: {str(e)}")

    new_url = f"/files/{file_name}"
    full_url = f"https://mp4-downloader-zxeu.onrender.com{new_url}"

    return {
        "original_url": url,
        "new_url": new_url,
        "full_url": full_url,
        "note": "הקובץ זמני! הורד מיד. yt-dlp משמש עם generic extractor לקישורים ישירים."
    }

@app.get("/")
async def root():
    return {
        "message": "ברוכים הבאים! שלח /download?url=... (תומך גם בקישורי googlevideo ישירים)",
        "docs": "/docs"
    }
