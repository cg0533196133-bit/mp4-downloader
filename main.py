from fastapi import FastAPI, HTTPException
import requests
import os
from uuid import uuid4

app = FastAPI()

DOWNLOAD_DIR = "/tmp/downloads"  # Render משתמש ב-/tmp – קבצים זמניים
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/download")
async def download_video(url: str):
    if not url.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="URL must end with .mp4")

    file_name = f"{uuid4()}.mp4"
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download: {str(e)}")

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Render נותן URL חיצוני אוטומטי, אבל קבצים ב-/tmp לא נגישים ישירות
    # לכן – החזר קישור זמני או שקול שמירה אחרת (ראה הערות למטה)
    new_url = f"/files/{file_name}"  # נצטרך להוסיף static files בהמשך

    return {"new_url": new_url, "note": "קבצים זמניים בלבד - הם נמחקים כשהאפליקציה ישנה"}
