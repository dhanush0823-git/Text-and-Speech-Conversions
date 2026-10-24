"""Backend tests. Run from the project root:  python -m pytest -v

Fast tests never load an AI model. Model tests download/run real models and are
skipped unless you set VOXAURA_RUN_MODEL_TESTS=1 (first run can take several minutes).
"""
import glob
import io
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
RUN_MODELS = os.getenv("VOXAURA_RUN_MODEL_TESTS") == "1"


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "/static/style.css" in r.text and "/static/app.js" in r.text


def test_static_assets():
    css = client.get("/static/style.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200 and "text/css" in css.headers["content-type"]
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and "tts_loaded" in body


def test_config():
    body = client.get("/api/config").json()
    assert body["voices"] and "base" in body["whisper_models"]


@pytest.mark.parametrize("payload", [
    {"text": "", "voice": "af_heart"},
    {"text": "   ", "voice": "af_heart"},
    {"text": "hello", "voice": "not_a_voice"},
    {"text": "hello", "voice": "af_heart", "speed": 5},
    {"text": "x" * 6000, "voice": "af_heart"},
])
def test_tts_rejects_bad_requests(payload):
    assert client.post("/api/tts", json=payload).status_code in (400, 413)


def test_tts_missing_fields():
    assert client.post("/api/tts", json={}).status_code == 422


def test_transcribe_rejects_unsupported_extension():
    r = client.post("/api/transcribe", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_transcribe_rejects_empty_file():
    r = client.post("/api/transcribe", files={"file": ("empty.wav", b"", "audio/wav")})
    assert r.status_code == 400


def test_transcribe_rejects_bad_model_and_language():
    f = {"file": ("a.wav", b"data", "audio/wav")}
    assert client.post("/api/transcribe", files=f, data={"model": "huge"}).status_code == 400
    f = {"file": ("a.wav", b"data", "audio/wav")}
    assert client.post("/api/transcribe", files=f, data={"language": "../etc"}).status_code == 400


def test_transcribe_missing_file():
    assert client.post("/api/transcribe").status_code == 422


def test_transcribe_cleans_temp_files_on_failure():
    before = set(glob.glob(os.path.join(tempfile.gettempdir(), "voxaura_*")))
    # Not real audio: decoding fails (or the engine is unavailable) but the temp file must be removed.
    client.post("/api/transcribe", files={"file": ("bad.wav", b"not audio", "audio/wav")}, data={"model": "tiny"})
    after = set(glob.glob(os.path.join(tempfile.gettempdir(), "voxaura_*")))
    assert after == before


@pytest.mark.skipif(not RUN_MODELS, reason="set VOXAURA_RUN_MODEL_TESTS=1 to run real model tests")
def test_tts_then_transcribe_roundtrip():
    r = client.post("/api/tts", json={"text": "Hello world, this is a test.", "voice": "af_heart"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content[:4] == b"RIFF" and r.content[8:12] == b"WAVE"
    assert "voxaura-speech.wav" in r.headers["content-disposition"]

    t = client.post(
        "/api/transcribe",
        files={"file": ("speech.wav", io.BytesIO(r.content), "audio/wav")},
        data={"model": "tiny", "language": "en"},
    )
    assert t.status_code == 200
    body = t.json()
    assert "hello" in body["text"].lower()
    assert body["language"] == "en"
