import os, uuid, time, threading
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

BASE_URL = "https://mp4-downloader-zxeu.onrender.com"
VIDEO_DIR = "static/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

jobs = {}  # job_id -> status / url

def record_job(job_id, url, seconds):
    jobs[job_id] = {"status": "recording"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=VIDEO_DIR,
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)

        try:
            page.keyboard.press("k")  # YouTube
        except:
            pass

        time.sleep(seconds)
        context.close()
        browser.close()

    mp4 = next(f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4"))
    final = f"{job_id}.mp4"
    os.rename(os.path.join(VIDEO_DIR, mp4),
              os.path.join(VIDEO_DIR, final))

    jobs[job_id] = {
        "status": "done",
        "url": f"{BASE_URL}/static/videos/{final}"
    }

@app.route("/start")
def start():
    url = request.args.get("url")
    seconds = int(request.args.get("seconds", 20))
    if not url:
        return jsonify({"error": "missing url"}), 400

    job_id = str(uuid.uuid4())
    threading.Thread(
        target=record_job,
        args=(job_id, url, seconds),
        daemon=True
    ).start()

    return jsonify({
        "job_id": job_id,
        "status": "recording"
    })

@app.route("/status/<job_id>")
def status(job_id):
    return jsonify(jobs.get(job_id, {"status": "not_found"}))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
