# VoxAura — AI Text & Speech Converter

*Your words, transformed into sound.*

A local web app with exactly two tools:

- **Text to Speech** — [Kokoro](https://github.com/hexgrad/kokoro) turns text into a downloadable WAV file.
- **Speech to Text** — [faster-whisper](https://github.com/SYSTRAN/faster-whisper) transcribes a microphone recording or an uploaded audio file.

It is a converter, not a chatbot. No accounts, no analytics, no telemetry.

## Required Python version: 3.12

Kokoro 0.9.x declares `Requires-Python >=3.10,<3.13`, so it cannot be installed on Python 3.13
(this is the cause of the `Could not find a version that satisfies the requirement kokoro>=0.9.4` error).
faster-whisper supports 3.9+, so **3.12** satisfies both.

Check what you have:

```powershell
py --list
python --version
```

Install 3.12 alongside your other versions (this does not change your other projects):

```powershell
winget install Python.Python.3.12
```

or download it from https://www.python.org/downloads/windows/. VoxAura uses its own `.venv`
folder, so other Python environments are untouched.

## Quick start (Windows 11)

From the project folder in PowerShell:

```powershell
.\start_voxaura.bat
```

(Double-clicking the file in File Explorer also works.) The script finds Python 3.12, creates `.venv`
if needed, installs `requirements.txt` only when it changed, and starts the server.
**The first install downloads PyTorch and other packages and can take several minutes.**

Then open **http://127.0.0.1:8000** in your browser. Do not open `static/index.html` directly from the
file system: the page must be served by the local server so `/static/style.css` and `/static/app.js` load.

Stop the app with `Ctrl+C` in the terminal window.

If `.venv` already exists but was made with another Python version, the script stops and explains
what to do. It never deletes anything automatically.

### Manual setup (what the script does)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## Using the app

**Text to Speech:** type or paste text (max 5000 characters), choose a voice and speed, click
*Generate Speech*, then play it or click *Download WAV*.

**Speech to Text:** either *Start Recording* → *Stop Recording*, or choose an audio file
(WAV, MP3, M4A, WebM, MP4, OGG, FLAC, AAC; max 50 MB, 30 minutes). Pick a model and language
(automatic detection by default), click *Transcribe Audio*, then edit, copy, or download the transcript as TXT.

## Models and downloads

Nothing is downloaded until you use a feature for the first time.

| Feature | Model | Source | License | Approx. size |
|---|---|---|---|---|
| Text to Speech | Kokoro-82M | Hugging Face `hexgrad/Kokoro-82M` | Apache-2.0 | ~330 MB |
| Speech to Text | Whisper via faster-whisper (tiny/base/small/medium) | Hugging Face (Systran) | MIT | ~75 MB / 145 MB / 480 MB / 1.5 GB |

Kokoro's English text processing (misaki) may also download a small spaCy language model on first use.
The app runs locally, but **installation and first use need internet access** to fetch packages and models.
After everything is cached it should work offline, but this has not been verified on every setup.

### CPU and memory

Everything runs on the CPU by default (`int8` for Whisper). Larger Whisper models are more accurate but
slower and use more RAM (`medium` may need around 5 GB). `base` is the default. To change device or
precision, set `VOXAURA_WHISPER_DEVICE` / `VOXAURA_WHISPER_COMPUTE_TYPE` (see `.env.example`);
GPU use needs separate NVIDIA libraries and is not required.

Audio decoding uses PyAV, which ships with faster-whisper, so **no separate ffmpeg install is needed**.

## API

```powershell
curl http://127.0.0.1:8000/api/health

curl -X POST http://127.0.0.1:8000/api/tts -H "Content-Type: application/json" `
  -d '{\"text\":\"Hello from VoxAura\",\"voice\":\"af_heart\",\"speed\":1.0}' --output speech.wav

curl -X POST http://127.0.0.1:8000/api/transcribe -F "file=@speech.wav" -F "model=base" -F "language=auto"
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

Fast tests never load a model. The real model round-trip test (text → speech → text) downloads models
and is opt-in: `$env:VOXAURA_RUN_MODEL_TESTS = "1"` before running pytest.

## Troubleshooting

- **Python version / Kokoro install error:** you are using Python 3.13 or newer. Install 3.12 (above), delete `.venv` yourself, and rerun the script.
- **Kokoro or package installation fails:** read the first error in the log; check your connection and rerun the script (it retries because the install stamp is only written on success).
- **Missing model files / first request is slow or fails:** the model is still downloading or the download was blocked. Check the terminal window, then try again.
- **Port 8000 already in use:** run `.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8001` and open `http://127.0.0.1:8001`.
- **Microphone does not work:** allow microphone access for `127.0.0.1` in your browser's site settings; check that a microphone is connected. Uploading a file is an alternative.
- **"Could not transcribe this audio":** the file may be corrupted or in an unusual encoding. Convert it to WAV or MP3 and retry.
- **Page looks unstyled / buttons do nothing:** you probably opened the HTML file directly. Use `http://127.0.0.1:8000`. Confirm `/static/style.css` and `/static/app.js` open in the browser.

## Privacy

Audio you record or upload is written to a temporary file for the duration of a single request and then deleted.
Generated speech is returned to your browser and not kept on disk. There is no analytics or telemetry.

## Project layout

```
voxaura-genai/
├── backend/        FastAPI app (main.py)
├── static/         index.html, style.css, app.js
├── tests/          test_api.py
├── requirements.txt / requirements-dev.txt
├── start_voxaura.bat
└── .env.example
```
