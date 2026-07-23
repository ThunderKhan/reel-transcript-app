# reel-transcript

A tiny local web app: paste an Instagram reel URL, it downloads the video,
extracts the audio, and transcribes it with Whisper — all running on your
own machine.

## Setup

```bash
pip install flask yt-dlp openai-whisper --break-system-packages
```

You also need `ffmpeg` installed and on your PATH:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Windows: download from ffmpeg.org and add it to PATH

## Run

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

## Using it

1. Paste a reel URL (e.g. `https://www.instagram.com/reel/XXXXXXX/`)
2. Pick a Whisper model size — `base` is a good default; `medium` is slower
   but more accurate
3. Click **run** and watch the pipeline (download → audio → transcribe)
4. Copy the transcript once it's done

## Notes

- First run of a given model size downloads Whisper's weights, which can
  take a minute or two.
- Private or login-gated reels need cookies. You can add
  `--cookies cookies.txt` support in `download_reel()` in `app.py` if needed.
- This is meant for personal use on your own content or content you have
  rights to — Instagram's Terms of Service restrict scraping.
- Jobs run in a background thread and are tracked in memory, so restarting
  the server clears any in-progress jobs.
