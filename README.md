<div align="center">

# 🎙️ VoxAura

### AI-Powered Text-to-Speech & Speech-to-Text

**Transform text into natural-sounding speech. Turn spoken words into editable text.**

A locally running AI-powered web application combining **Kokoro TTS** and **Faster-Whisper** in one elegant, easy-to-use interface.

<br>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![Kokoro](https://img.shields.io/badge/Kokoro-Text--to--Speech-7C3AED?style=for-the-badge)
![Whisper](https://img.shields.io/badge/Faster--Whisper-Speech--to--Text-14B8A6?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-F7DF1E?style=for-the-badge\&logo=javascript\&logoColor=black)

<br>

**Two AI capabilities. One unified experience.**

</div>

---

## ✨ Overview

**VoxAura** is a Python-powered web application that makes speech technology accessible through two practical AI workflows:

* **Text-to-Speech (TTS):** Convert written content into audio using Kokoro TTS.
* **Speech-to-Text (STT):** Transcribe microphone recordings and uploaded audio files into editable text using Faster-Whisper.

Built with **FastAPI, HTML, CSS, and JavaScript**, VoxAura combines AI inference with a responsive frontend and a straightforward local setup.

Instead of relying on a complicated desktop interface, users can perform both conversions directly in their browser while the Python backend handles model inference.

> **Project philosophy:** Useful AI, minimal friction, and a focused user experience.

## 🚀 Features

<table>
<tr>
<td width="50%">

### 🔊 Text-to-Speech

* Convert text into spoken audio.
* Generate speech using Kokoro TTS.
* Select from supported voices.
* Listen to generated audio in the browser.
* Download speech as a WAV file.
* Receive feedback during generation.

</td>
<td width="50%">

### 🎧 Speech-to-Text

* Record audio using your microphone.
* Upload supported audio files.
* Transcribe speech using Faster-Whisper.
* Choose a transcription model.
* Select a language or use automatic detection, where supported.
* Edit, copy, and download transcripts.

</td>
</tr>
<tr>
<td width="50%">

### 🎨 Modern Interface

* Dark, premium visual design.
* Responsive conversion cards.
* Clear loading and error states.
* Browser-based audio playback.
* Simple, accessible controls.

</td>
<td width="50%">

### ⚙️ Local AI Processing

* Python-based inference backend.
* Local model execution after required assets are downloaded.
* Dedicated virtual environment.
* No chatbot or unrelated AI features.
* Independent TTS and STT workflows.

</td>
</tr>
</table>

---

## 🧠 How It Works

### 1. Text-to-Speech Pipeline

```text
User enters text
       │
       ▼
HTML / JavaScript Frontend
       │
       ▼
FastAPI: POST /api/tts
       │
       ▼
Kokoro TTS Pipeline
       │
       ▼
Generated Speech Audio
       │
       ▼
WAV Playback & Download
```

### 2. Speech-to-Text Pipeline

```text
Microphone Recording / Audio Upload
                 │
                 ▼
          Browser Frontend
                 │
                 ▼
      FastAPI: POST /api/transcribe
                 │
                 ▼
       Audio Input Processing
                 │
                 ▼
          Faster-Whisper
                 │
                 ▼
       Speech Recognition
                 │
                 ▼
       Editable Transcript
                 │
                 ▼
          Copy / Download
```

These pipelines operate independently, allowing users to choose the conversion they need.

---

## 🛠️ Technology Stack

| Technology         | Purpose                                     |
| ------------------ | ------------------------------------------- |
| Python 3.12        | Backend runtime                             |
| FastAPI            | REST API and application server             |
| Uvicorn            | ASGI server                                 |
| Kokoro TTS         | Text-to-speech generation                   |
| Faster-Whisper     | Automatic speech recognition                |
| CTranslate2        | Efficient Whisper inference                 |
| PyAV               | Audio decoding                              |
| HTML5              | Application structure                       |
| CSS3               | Responsive styling and visual design        |
| Vanilla JavaScript | Frontend interactions and API communication |
| MediaRecorder API  | Browser microphone recording                |
| NumPy / SoundFile  | Audio processing, where required            |

### Why this stack?

* **FastAPI** provides a lightweight API layer for AI inference.
* **Kokoro TTS** handles speech synthesis.
* **Faster-Whisper** provides transcription using Whisper models.
* **Vanilla JavaScript** keeps the frontend lightweight without requiring a separate JavaScript build process.
* **PyAV** supports the audio-decoding workflow used by Faster-Whisper.

---

## 📁 Project Structure

```text
voxaura-genai/
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── tests/
│   └── test_api.py
│
├── .venv/
│
├── requirements.txt
├── start_voxaura.bat
├── README.md
└── .gitignore
```

### Folder responsibilities

* `backend/main.py` — FastAPI routes, model initialization, audio generation, and transcription.
* `static/index.html` — Main application interface.
* `static/style.css` — Layout, responsive design, and visual styling.
* `static/app.js` — Browser interactions, recording, API requests, and conversion results.
* `tests/test_api.py` — Backend API tests.
* `requirements.txt` — Python dependencies.
* `start_voxaura.bat` — Windows startup and environment setup.
* `.gitignore` — Excludes virtual environments, caches, and other local artifacts.

*The structure above assumes these files exist in your current project. Keep the README consistent with your actual repository if your folder structure differs.*

---

## 💻 Installation & Setup

### Prerequisites

* Windows 10 or Windows 11.
* Python 3.12, compatible with the selected dependency versions.
* Internet access for initial dependency and model downloads.
* Sufficient disk space and memory for the selected AI models.

> **Important:** Use the project's compatible Python environment. Python 3.13 may not support every Kokoro dependency used by this project.

### Step 1 — Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Navigate into the project:

```bash
cd voxaura-genai
```

Replace the placeholder repository URL with your actual GitHub repository URL.

### Step 2 — Create a virtual environment

If Python 3.12 is installed:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can invoke the virtual environment's Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe --version
```

### Step 3 — Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Install the project requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Dependency compatibility matters.** Keep the tested PyAV version pinned in `requirements.txt`. In the current Windows environment, PyAV `16.1.0` resolved the `metadata_errors` API incompatibility encountered with PyAV `19.0.2`.

If you are configuring a fresh environment, use a mutually compatible set of `faster-whisper` and PyAV versions.

### Step 4 — Start VoxAura

Run the Windows startup script:

```powershell
.\start_voxaura.bat
```

Wait until Uvicorn reports that the application has started.

### Step 5 — Open the application

Visit:

**http://127.0.0.1:8000**

You can now use the Text-to-Speech and Speech-to-Text interfaces.

---

## 🎯 Usage Guide

### Text-to-Speech

1. Open VoxAura in your browser.
2. Enter or paste text into the text input.
3. Choose a supported voice.
4. Click **Generate Speech**.
5. Wait for generation to complete.
6. Play the generated audio.
7. Download the resulting WAV file.

### Speech-to-Text

1. Open the Speech-to-Text panel.
2. Record audio with your microphone or upload a supported audio file.
3. Choose the transcription model.
4. Select a language or automatic detection, if available.
5. Click **Transcribe Audio**.
6. Review the generated transcript.
7. Edit, copy, or download the text.

**Tip:** Start with a smaller transcription model when testing the application on a CPU. Larger models can improve recognition in some cases but generally require more memory and processing time.

---

## 🔌 API Endpoints

The FastAPI backend exposes the following application endpoints.

| Method | Endpoint          | Purpose                         |
| ------ | ----------------- | ------------------------------- |
| `GET`  | `/`               | Serve the VoxAura interface     |
| `GET`  | `/api/health`     | Check application health        |
| `GET`  | `/api/config`     | Retrieve frontend configuration |
| `POST` | `/api/tts`        | Generate speech from text       |
| `POST` | `/api/transcribe` | Transcribe an audio upload      |

### Example health check

Open the following address in your browser:

`http://127.0.0.1:8000/api/health`

The response should indicate whether the backend is running.

### Interactive API documentation

FastAPI typically provides interactive API documentation at:

`http://127.0.0.1:8000/docs`

Use the documentation to inspect available endpoints and their request formats.

---

## ⚡ Performance Considerations

AI inference performance depends on hardware, model size, audio duration, and input length.

### Faster-Whisper

* Smaller models are generally faster and use less memory.
* Larger models can offer improved recognition quality for some audio.
* CPU inference is supported, although it may take longer.
* Initial model downloads require internet access.

### Kokoro TTS

* Speech generation time depends on the input length and available hardware.
* Initial setup may download required model assets.
* Reusing an initialized pipeline can avoid unnecessary model-loading overhead.

VoxAura is designed for local development rather than guaranteed real-time processing.

---

## 🔧 Troubleshooting

### 1. Python version incompatibility

Check the active project interpreter:

```powershell
.\.venv\Scripts\python.exe --version
```

Use a supported Python version and recreate the virtual environment only when necessary.

### 2. PyAV `metadata_errors` error

If you encounter:

```text
TypeError: open() got an unexpected keyword argument 'metadata_errors'
```

Check the installed dependency versions:

```powershell
.\.venv\Scripts\python.exe -m pip show faster-whisper av
```

The versions must be compatible. In the development environment, PyAV `16.1.0` accepted the argument used by the installed Faster-Whisper audio decoder.

### 3. Model download or loading errors

Check:

* Internet connectivity.
* Available disk space.
* The server terminal for the actual exception.
* Whether the selected model has completed downloading.

### 4. Microphone access denied

Allow microphone access in your browser and Windows privacy settings. Check that the microphone works in another application.

### 5. Audio decoding errors

Try a supported audio format, such as WAV, and check the backend traceback for decoding errors.

### 6. Port 8000 is already in use

Stop the other process using the port or configure Uvicorn to use another available port.

### 7. CSS is not loading

Make sure VoxAura is opened through:

`http://127.0.0.1:8000`

Check that these resources are accessible:

* `http://127.0.0.1:8000/static/style.css`
* `http://127.0.0.1:8000/static/app.js`

---

## 🔐 Privacy & Local Processing

VoxAura is designed to run as a local web application.

* Audio processing is handled by the local Python backend after required models are available.
* The browser communicates with the backend running on your machine.
* Model and dependency downloads may contact external services during installation or first use.
* The project does not require a chatbot or a cloud-based conversational API.

Actual privacy behavior depends on the implementation and configuration of the running application. Avoid uploading sensitive audio unless you understand how your local setup handles temporary files.

---

## 🧪 Testing

Run the backend tests using:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/
```

This command assumes `pytest` is installed in the project environment.

For manual testing, verify:

* The homepage loads with the expected styling.
* The health endpoint responds.
* Text-to-speech generates playable WAV audio.
* Speech-to-text accepts supported recordings.
* Transcription results can be copied and downloaded.
* Errors are handled without leaving controls permanently disabled.

Model-level tests may require downloaded model assets and additional processing time.

---

## 🗺️ Future Improvements

Potential future enhancements include:

* Additional supported Kokoro voices.
* Improved audio playback controls.
* Subtitle and transcript export formats.
* More detailed transcription progress feedback.
* Additional automated tests.
* Performance improvements for longer recordings.

These are possible future directions, not claims about existing functionality.

---

## 👨‍💻 Project Purpose

VoxAura demonstrates how modern AI models can be integrated into a practical web application using a lightweight frontend and a Python backend.

The project combines:

* AI model integration.
* Speech synthesis.
* Automatic speech recognition.
* REST API development.
* Browser audio capture.
* Audio file processing.
* Responsive UI development.
* Python dependency management and troubleshooting.

It provides a practical foundation for exploring speech AI and full-stack application development.

---

<div align="center">

### VoxAura

**From text to voice. From voice to text.**

Built with Python, FastAPI, Kokoro TTS, Faster-Whisper, and JavaScript.

</div>
