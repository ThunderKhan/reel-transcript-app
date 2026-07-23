#!/usr/bin/env python3
"""
app.py — Flask backend for the Reel Transcript tool.

Serves a local webpage where you paste an Instagram reel URL,
and runs the download -> extract audio -> transcribe pipeline
in the background, returning the transcript to the page.

Run with:
    pip install flask yt-dlp openai-whisper --break-system-packages
    python app.py

Then open http://localhost:5000 in your browser.
"""

import subprocess
import tempfile
import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# In-memory job store: job_id -> {"status": ..., "transcript": ..., "error": ...}
JOBS: dict[str, dict] = {}

# Cache loaded whisper models by size so we don't reload on every request
_MODEL_CACHE: dict[str, object] = {}


def get_model(model_size: str):
    import whisper
    if model_size not in _MODEL_CACHE:
        _MODEL_CACHE[model_size] = whisper.load_model(model_size)
    return _MODEL_CACHE[model_size]


def download_reel(url: str, dest_dir: Path) -> Path:
    output_template = str(dest_dir / "reel.%(ext)s")
    subprocess.run(["yt-dlp", url, "-o", output_template], check=True)
    downloaded = list(dest_dir.glob("reel.*"))
    if not downloaded:
        raise FileNotFoundError("yt-dlp did not produce an output file.")
    return downloaded[0]


def extract_audio(video_path: Path, dest_dir: Path) -> Path:
    audio_path = dest_dir / "audio.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "mp3", str(audio_path)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return audio_path


def run_job(job_id: str, url: str, model_size: str):
    try:
        JOBS[job_id]["status"] = "downloading"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            video_path = download_reel(url, tmp_dir)

            JOBS[job_id]["status"] = "extracting audio"
            audio_path = extract_audio(video_path, tmp_dir)

            JOBS[job_id]["status"] = "transcribing"
            model = get_model(model_size)
            result = model.transcribe(str(audio_path))

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["transcript"] = result["text"].strip()
    except subprocess.CalledProcessError as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = f"External tool failed: {e}"
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json(force=True)
    url = (data or {}).get("url", "").strip()
    model_size = (data or {}).get("model", "base")

    if not url:
        return jsonify({"error": "Please provide a reel URL."}), 400

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "queued", "transcript": None, "error": None}

    thread = threading.Thread(target=run_job, args=(job_id, url, model_size), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job id."}), 404
    return jsonify(job)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
