from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = FastAPI(title="MP4 Downloader with yt-dlp", description="Supports YouTube URLs + direct video links")

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/download")
async def download_video(url: str):
    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'continuedl': True,
        'retries': 10,
        'fragment_retries': 10,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',          # ← כאן! הקובץ חייב להיות באותה תיקייה כמו main.py
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
        },
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 10000:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception("ההורדה נכשלה – כנראה קובץ לא תקין (HTML/ריק)")

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
        "note": "קובץ זמני – הורד מיד!"
    }

@app.get("/")
async def root():
    return {"message": "OK – השתמש ב-/download?url=..."}
