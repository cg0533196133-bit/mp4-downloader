from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import requests
import os
from uuid import uuid4
import random  # להוסיף random לבחירה רנדומלית

app = FastAPI(title="MP4 Downloader", description="Downloader proxy for MP4 files - temporary storage only")

# תיקייה זמנית - ב-Render Free Tier הכול נמחק כשהאפליקציה ישנה (~15 דק')
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# מאפשר גישה ישירה לקבצים דרך /files/...
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

# רשימת פרוקסי חינמיים (עדכנית מ-2026 – HTTPS proxies)
PROXIES_LIST = [
    "http://195.158.8.123:3128",    # Uzbekistan
    "http://94.177.58.26:7443",      # Germany
    "http://193.24.120.242:1401",    # Iran
    "http://147.75.34.105:443",      # Netherlands
    "http://195.133.11.246:1080",    # Russia
    "http://212.47.232.28:80",       # France
    "http://163.5.128.97:14270",     # United States
    "http://185.233.202.217:5858",   # Netherlands
    "http://89.22.237.70:80",        # Sweden
    "http://178.239.145.119:80",     # Iran
]

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

    # מערבב את הרשימה כדי לבחור רנדומלי
    random.shuffle(PROXIES_LIST)
    success = False
    error_msg = ""

    # נסה עד 3 פרוקסי
    for i in range(min(3, len(PROXIES_LIST))):
        proxy = PROXIES_LIST[i]
        proxies = {"http": proxy, "https": proxy}
        try:
            print(f"מנסה פרוקסי: {proxy}")  # ללוגים – אפשר למחוק
            response = requests.get(
                url,
                stream=True,
                timeout=120,
                headers=headers,
                allow_redirects=True,
                proxies=proxies
            )
            response.raise_for_status()
            success = True
            break
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"שגיאה עם פרוקסי {proxy}: {str(http_err)} - סטטוס: {response.status_code if 'response' in locals() else 'לא ידוע'}"
        except Exception as e:
            error_msg = f"שגיאה עם פרוקסי {proxy}: {str(e)}"

    if not success:
        raise HTTPException(status_code=400, detail=f"כל הפרוקסי נכשלו: {error_msg}. נסה להחליף פרוקסי ברשימה.")

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
