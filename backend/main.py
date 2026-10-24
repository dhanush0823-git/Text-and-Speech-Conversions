"""VoxAura backend: FastAPI app serving the UI plus /api/tts and /api/transcribe.

Heavy libraries (kokoro, faster-whisper) are imported lazily so the server starts
instantly and the static/health endpoints work even before models are downloaded.
"""
import io
import logging
import os
import re
import tempfile
import threading
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger("voxaura")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# ---- Configuration (override with environment variables) --------------------
MAX_TEXT_CHARS = int(os.getenv("VOXAURA_MAX_TEXT_CHARS", "5000"))
MAX_UPLOAD_BYTES = int(os.getenv("VOXAURA_MAX_UPLOAD_MB", "50")) * 1024 * 1024
MAX_AUDIO_SECONDS = int(os.getenv("VOXAURA_MAX_AUDIO_SECONDS", "1800"))
WHISPER_DEVICE = os.getenv("VOXAURA_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("VOXAURA_WHISPER_COMPUTE_TYPE", "int8")

KOKORO_SAMPLE_RATE = 24000
# The first letter of a Kokoro voice id is its language code ('a' = American, 'b' = British).
VOICES = {
    "af_heart": "Heart · US female",
    "af_bella": "Bella · US female",
    "af_nicole": "Nicole · US female",
    "af_sarah": "Sarah · US female",
    "am_adam": "Adam · US male",
    "am_michael": "Michael · US male",
    "bf_emma": "Emma · UK female",
    "bf_isabella": "Isabella · UK female",
    "bm_george": "George · UK male",
    "bm_lewis": "Lewis · UK male",
}
WHISPER_MODELS = ["tiny", "base", "small", "medium"]
DEFAULT_WHISPER_MODEL = "base"
ALLOWED_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".webm", ".mp4", ".ogg", ".opus", ".flac", ".aac",
}
LANGUAGE_RE = re.compile(r"^[a-z]{2,3}$")
SPEED_MIN, SPEED_MAX = 0.7, 1.3

app = FastAPI(title="VoxAura", docs_url=None, redoc_url=None)

# ---- Lazy model caches -------------------------------------------------------
_tts_pipelines: dict = {}
_tts_lock = threading.Lock()
_whisper_models: dict = {}
_whisper_lock = threading.Lock()
_tts_infer_lock = threading.Lock()  # one TTS generation at a time keeps memory predictable
_stt_infer_lock = threading.Lock()


def _get_tts_pipeline(lang_code: str):
    with _tts_lock:
        if lang_code not in _tts_pipelines:
            from kokoro import KPipeline  # imported lazily: pulls in torch

            logger.info("Loading Kokoro pipeline (lang_code=%s)...", lang_code)
            _tts_pipelines[lang_code] = KPipeline(lang_code=lang_code)
        return _tts_pipelines[lang_code]


def _get_whisper_model(size: str):
    with _whisper_lock:
        if size not in _whisper_models:
            from faster_whisper import WhisperModel

            logger.info("Loading faster-whisper model '%s'...", size)
            _whisper_models[size] = WhisperModel(
                size, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
            )
        return _whisper_models[size]


# ---- Request models ----------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    voice: str
    speed: float = 1.0


def _error(status: int, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail=message)


# ---- Synthesis ---------------------------------------------------------------
def _synthesize(text: str, voice: str, speed: float) -> bytes:
    import numpy as np
    import soundfile as sf

    pipeline = _get_tts_pipeline(voice[0])
    chunks = []
    with _tts_infer_lock:
        # KPipeline yields (graphemes, phonemes, audio) per text segment at 24 kHz.
        for _gs, _ps, audio in pipeline(text, voice=voice, speed=speed):
            if audio is None:
                continue
            if hasattr(audio, "detach"):  # torch.Tensor -> numpy
                audio = audio.detach().cpu().numpy()
            chunks.append(np.asarray(audio, dtype="float32").reshape(-1))
    if not chunks:
        raise ValueError("Kokoro produced no audio for this text.")
    buffer = io.BytesIO()
    sf.write(buffer, np.concatenate(chunks), KOKORO_SAMPLE_RATE, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


@app.post("/api/tts")
async def tts(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise _error(400, "Please enter some text to convert.")
    if len(text) > MAX_TEXT_CHARS:
        raise _error(413, f"Text is too long. The limit is {MAX_TEXT_CHARS} characters.")
    if req.voice not in VOICES:
        raise _error(400, "Unsupported voice selected.")
    if not (SPEED_MIN <= req.speed <= SPEED_MAX):
        raise _error(400, f"Speed must be between {SPEED_MIN} and {SPEED_MAX}.")
    try:
        wav_bytes = await run_in_threadpool(_synthesize, text, req.voice, req.speed)
    except ImportError:
        logger.exception("Kokoro import failed")
        raise _error(500, "The Kokoro TTS engine is not installed correctly. See the README troubleshooting section.")
    except Exception:
        logger.exception("TTS generation failed")
        raise _error(500, "Speech generation failed. If this is the first run, model files may not have finished downloading. Check the server console for details.")
    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="voxaura-speech.wav"'},
    )


# ---- Transcription -----------------------------------------------------------
def _transcribe(path: str, model_size: str, language):
    started = time.perf_counter()
    model = _get_whisper_model(model_size)
    with _stt_infer_lock:
        segments, info = model.transcribe(
            path, language=language, beam_size=5, vad_filter=True
        )
        if info.duration and info.duration > MAX_AUDIO_SECONDS:
            raise OverflowError
        text = " ".join(seg.text.strip() for seg in segments).strip()  # generator: runs inference here
    return {
        "text": text,
        "language": info.language,
        "language_probability": round(float(info.language_probability), 3),
        "audio_duration_seconds": round(float(info.duration), 2) if info.duration else None,
        "processing_seconds": round(time.perf_counter() - started, 2),
    }


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_WHISPER_MODEL),
    language: str = Form("auto"),
):
    if model not in WHISPER_MODELS:
        raise _error(400, "Unsupported model size.")
    language = language.strip().lower()
    if language != "auto" and not LANGUAGE_RE.match(language):
        raise _error(400, "Invalid language code.")
    # Only the extension of the client filename is used; the temp path is generated by us.
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise _error(415, "Unsupported audio format. Use WAV, MP3, M4A, WebM, MP4, OGG, FLAC or AAC.")

    tmp = tempfile.NamedTemporaryFile(prefix="voxaura_", suffix=ext, delete=False)
    tmp_path = tmp.name
    try:
        size = 0
        with tmp:
            while True:
                block = await file.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                if size > MAX_UPLOAD_BYTES:
                    raise _error(413, f"File too large. The limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
                tmp.write(block)
        if size == 0:
            raise _error(400, "The uploaded audio file is empty.")
        try:
            result = await run_in_threadpool(
                _transcribe, tmp_path, model, None if language == "auto" else language
            )
        except OverflowError:
            raise _error(413, f"Audio is too long. The limit is {MAX_AUDIO_SECONDS // 60} minutes.")
        except ImportError:
            logger.exception("faster-whisper import failed")
            raise _error(500, "The faster-whisper engine is not installed correctly. See the README troubleshooting section.")
        except Exception:
            logger.exception("Transcription failed")
            raise _error(422, "Could not transcribe this audio. The file may be corrupted or in an unsupported encoding, or the model could not be loaded (check the server console).")
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---- Info / health / frontend ------------------------------------------------
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "tts_loaded": bool(_tts_pipelines),
        "stt_models_loaded": sorted(_whisper_models.keys()),
    }


@app.get("/api/config")
async def config():
    return {
        "voices": [{"id": k, "label": v} for k, v in VOICES.items()],
        "whisper_models": WHISPER_MODELS,
        "default_whisper_model": DEFAULT_WHISPER_MODEL,
        "max_text_chars": MAX_TEXT_CHARS,
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        "speed_min": SPEED_MIN,
        "speed_max": SPEED_MAX,
    }


@app.exception_handler(Exception)
async def unhandled(_request, _exc):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
