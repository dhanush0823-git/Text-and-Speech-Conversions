// VoxAura frontend. Plain JavaScript, no build step, no external requests.
"use strict";

const $ = (id) => document.getElementById(id);
const show = (el, on = true) => { el.hidden = !on; };

// Limits and voices are loaded from /api/config; these are fallbacks.
let MAX_CHARS = 5000;
let MAX_UPLOAD_MB = 50;
const ALLOWED_EXT = ["wav", "mp3", "m4a", "webm", "mp4", "ogg", "opus", "flac", "aac"];

// Turn a failed fetch Response into a readable message (never shows tracebacks).
async function readError(res) {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return "The request was not valid. Please check your input.";
  } catch (_) { /* not JSON */ }
  return `The server returned an error (${res.status}).`;
}
const networkMessage = "Could not reach the VoxAura server. Make sure the app is still running in its terminal window.";

// ---------- Server status + config ----------
async function checkHealth() {
  try {
    const res = await fetch("/api/health", { cache: "no-store" });
    if (!res.ok) throw new Error();
    $("statusDot").className = "dot ok";
    $("statusText").textContent = "Local server running";
  } catch (_) {
    $("statusDot").className = "dot bad";
    $("statusText").textContent = "Server unavailable";
  }
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error();
    const cfg = await res.json();
    MAX_CHARS = cfg.max_text_chars;
    MAX_UPLOAD_MB = cfg.max_upload_mb;
    const select = $("ttsVoice");
    select.innerHTML = "";
    cfg.voices.forEach((v) => select.add(new Option(v.label, v.id)));
    $("ttsSpeed").min = cfg.speed_min;
    $("ttsSpeed").max = cfg.speed_max;
  } catch (_) {
    showError("ttsError", networkMessage);
  }
  $("ttsText").maxLength = MAX_CHARS;
  updateCount();
}

function showError(id, msg) { const el = $(id); el.textContent = msg; show(el, true); }
function clearMsg(id) { const el = $(id); el.textContent = ""; show(el, false); }

// ---------- Text to Speech ----------
let ttsBusy = false;
let ttsUrl = null;

function updateCount() { $("ttsCount").textContent = `${$("ttsText").value.length} / ${MAX_CHARS}`; }
$("ttsText").addEventListener("input", updateCount);
$("ttsSpeed").addEventListener("input", () => {
  $("ttsSpeedOut").textContent = `${Number($("ttsSpeed").value).toFixed(2).replace(/0$/, "")}×`;
});

$("ttsClear").addEventListener("click", () => {
  $("ttsText").value = "";
  updateCount();
  clearMsg("ttsError"); clearMsg("ttsOk");
});

$("ttsGenerate").addEventListener("click", async () => {
  if (ttsBusy) return; // prevent duplicate submissions
  clearMsg("ttsError"); clearMsg("ttsOk");
  const text = $("ttsText").value.trim();
  if (!text) { showError("ttsError", "Please enter some text first."); return; }
  if (text.length > MAX_CHARS) { showError("ttsError", `Text is too long (limit ${MAX_CHARS} characters).`); return; }

  ttsBusy = true;
  $("ttsGenerate").disabled = true;
  show($("ttsBusy"), true);
  show($("ttsResult"), false);
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: $("ttsVoice").value, speed: Number($("ttsSpeed").value) }),
    });
    if (!res.ok) { showError("ttsError", await readError(res)); return; }
    const blob = await res.blob();
    if (ttsUrl) URL.revokeObjectURL(ttsUrl);
    ttsUrl = URL.createObjectURL(blob);
    $("ttsAudio").src = ttsUrl;
    $("ttsDownload").href = ttsUrl;
    show($("ttsResult"), true);
    const ok = $("ttsOk"); ok.textContent = "Speech generated. Press play or download the WAV file."; show(ok, true);
  } catch (_) {
    showError("ttsError", networkMessage);
  } finally {
    ttsBusy = false;
    $("ttsGenerate").disabled = false;
    show($("ttsBusy"), false);
  }
});

$("ttsAudio").addEventListener("error", () => {
  showError("ttsError", "Your browser could not play the generated audio. You can still download the WAV file.");
});

// ---------- Speech to Text: audio source (recording OR upload) ----------
let currentAudio = null;   // { blob, name }
let previewUrl = null;
let sttBusy = false;

function setAudio(blob, name) {
  currentAudio = { blob, name };
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(blob);
  $("sttPreview").src = previewUrl;
  show($("sttPreview"), true);
  $("sttTranscribe").disabled = sttBusy;
  clearMsg("sttError");
}

$("sttFile").addEventListener("change", () => {
  const file = $("sttFile").files[0];
  if (!file) return;
  const ext = file.name.split(".").pop().toLowerCase();
  if (!ALLOWED_EXT.includes(ext)) {
    showError("sttError", "Unsupported file type. Use WAV, MP3, M4A, WebM, MP4, OGG, FLAC or AAC.");
    $("sttFile").value = "";
    return;
  }
  if (file.size === 0) { showError("sttError", "That file is empty."); $("sttFile").value = ""; return; }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    showError("sttError", `File is too large (limit ${MAX_UPLOAD_MB} MB).`);
    $("sttFile").value = "";
    return;
  }
  $("sttFileName").textContent = `Selected: ${file.name}`;
  setAudio(file, file.name);
});

// ---------- Speech to Text: microphone recording ----------
let recorder = null;
let recStream = null;
let recChunks = [];
let recTimer = null;
let recStarted = 0;

function pickMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
  return candidates.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
}
function extensionFor(mime) {
  if (mime.includes("webm")) return "webm";
  if (mime.includes("ogg")) return "ogg";
  if (mime.includes("mp4")) return "m4a";
  if (mime.includes("wav")) return "wav";
  return "webm";
}
function fmtTime(ms) {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
function stopTracks() { if (recStream) recStream.getTracks().forEach((t) => t.stop()); recStream = null; }

$("recStart").addEventListener("click", async () => {
  clearMsg("sttError");
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    showError("sttError", "This browser does not support microphone recording. Try uploading a file instead.");
    return;
  }
  try {
    recStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    if (err.name === "NotAllowedError" || err.name === "SecurityError") {
      showError("sttError", "Microphone access was denied. Allow it in your browser's site settings and try again.");
    } else if (err.name === "NotFoundError" || err.name === "OverconstrainedError") {
      showError("sttError", "No microphone was found. Connect one or upload an audio file instead.");
    } else {
      showError("sttError", "Could not start the microphone.");
    }
    return;
  }
  try {
    const mime = pickMimeType();
    recorder = mime ? new MediaRecorder(recStream, { mimeType: mime }) : new MediaRecorder(recStream);
  } catch (_) {
    stopTracks();
    showError("sttError", "Recording is not supported by this browser. Try uploading a file instead.");
    return;
  }
  recChunks = [];
  recorder.addEventListener("dataavailable", (e) => { if (e.data.size) recChunks.push(e.data); });
  recorder.addEventListener("stop", () => {
    clearInterval(recTimer);
    stopTracks();
    const type = recorder.mimeType || "audio/webm";
    const blob = new Blob(recChunks, { type });
    $("recStatus").textContent = "Recorded";
    $("recStart").disabled = false;
    $("recStop").disabled = true;
    if (blob.size === 0) { showError("sttError", "The recording is empty. Please try again."); return; }
    $("sttFile").value = "";
    $("sttFileName").textContent = "Using your recording.";
    setAudio(blob, `recording.${extensionFor(type)}`);
  });
  recorder.start();
  recStarted = Date.now();
  $("recStatus").textContent = "Recording";
  $("recTime").textContent = "0:00";
  recTimer = setInterval(() => { $("recTime").textContent = fmtTime(Date.now() - recStarted); }, 250);
  $("recStart").disabled = true;
  $("recStop").disabled = false;
});

$("recStop").addEventListener("click", () => {
  if (recorder && recorder.state !== "inactive") recorder.stop();
});

// ---------- Speech to Text: transcription ----------
$("sttTranscribe").addEventListener("click", async () => {
  if (sttBusy || !currentAudio) return;
  clearMsg("sttError");
  sttBusy = true;
  $("sttTranscribe").disabled = true;
  show($("sttBusy"), true);
  try {
    const form = new FormData();
    form.append("file", currentAudio.blob, currentAudio.name);
    form.append("model", $("sttModel").value);
    form.append("language", $("sttLang").value);
    const res = await fetch("/api/transcribe", { method: "POST", body: form });
    if (!res.ok) { showError("sttError", await readError(res)); return; }
    const data = await res.json();
    $("sttTranscript").value = data.text;
    const parts = [];
    if (data.language) parts.push(`Detected language: ${data.language} (${Math.round(data.language_probability * 100)}% confidence)`);
    parts.push(`Processed in ${data.processing_seconds}s`);
    if (!data.text) parts.push("No speech was detected in this audio");
    $("sttInfo").textContent = parts.join(" · ");
  } catch (_) {
    showError("sttError", networkMessage);
  } finally {
    sttBusy = false;
    $("sttTranscribe").disabled = !currentAudio;
    show($("sttBusy"), false);
  }
});

$("sttCopy").addEventListener("click", async () => {
  const text = $("sttTranscript").value;
  if (!text) { showError("sttError", "There is no transcript to copy."); return; }
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    $("sttTranscript").select();
    if (!document.execCommand("copy")) { showError("sttError", "Copy failed. Select the text and copy it manually."); return; }
  }
  $("sttInfo").textContent = "Copied to clipboard.";
});

$("sttDownloadTxt").addEventListener("click", () => {
  const text = $("sttTranscript").value;
  if (!text) { showError("sttError", "There is no transcript to download."); return; }
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url; a.download = "voxaura-transcript.txt";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

$("sttClear").addEventListener("click", () => {
  $("sttTranscript").value = "";
  $("sttInfo").textContent = "";
  clearMsg("sttError");
});

// ---------- Init ----------
loadConfig();
checkHealth();
setInterval(checkHealth, 10000);
