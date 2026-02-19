import os
import uuid
import time
import threading
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

BASE_URL = "https://mp4-downloader-zxeu.onrender.com"
VIDEO_DIR = "static/videos"

os.makedirs(VIDEO_DIR, exist_ok=True)
jobs = {}  # job_id -> {"status": "recording"/"done"/"error", "url": ...}

def record_job(job_id, url, seconds):
    try:
        jobs[job_id] = {"status": "recording"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                record_video_dir=VIDEO_DIR,
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            page.goto(url, timeout=120000)
            page.wait_for_timeout(5000)

            # נסה להפעיל play ב־YouTube
            try:
                page.keyboard.press("k")
            except:
                pass

            start = time.time()
            while time.time() - start < seconds:
                time.sleep(1)

            context.close()
            browser.close()

        # שמירה כ-MP4
        mp4_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4") or f.endswith(".webm")]
        if mp4_files:
            mp4_file = mp4_files[0]
            final_name = f"{job_id}.mp4"
            os.rename(os.path.join(VIDEO_DIR, mp4_file),
                      os.path.join(VIDEO_DIR, final_name))
            jobs[job_id] = {"status": "done", "url": f"{BASE_URL}/static/videos/{final_name}"}
        else:
            jobs[job_id] = {"status": "error", "error": "No video generated"}

    except Exception as e:
        jobs[job_id] = {"status": "error", "error": str(e)}

@app.route("/")
def home():
    return "Recorder is running"

@app.route("/start")
def start():
    url = request.args.get("url")
    seconds = int(request.args.get("seconds", 20))
    if not url:
        return jsonify({"error": "missing url"}), 400
    job_id = str(uuid.uuid4())
    threading.Thread(target=record_job, args=(job_id, url, seconds)).start()
    return jsonify({"job_id": job_id, "status": "recording"})

@app.route("/status/<job_id>")
def status(job_id):
    return jsonify(jobs.get(job_id, {"status": "not_found"}))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
