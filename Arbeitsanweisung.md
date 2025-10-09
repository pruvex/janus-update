Alles klar. Ich liefere dir zwei Dinge:



Einen kompletten TTS-Service für das Backend (Piper via CLI mit Presets, Voice-Auswahl, Caching).

Eine präzise Arbeitsanweisung, damit dein Coding-Agent das in Janus umsetzt, inklusive UI-Einbindung der TTS- und Stimmenauswahl in den Einstellungen.


Teil 1: Backend-Code für TTS (FastAPI-Service)
Datei: backend/services/tts_service.py


Code:
from future import annotations


import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel


Konfiguration

Standard: piper im PATH; alternativ per ENV PIPER_EXE setzen.

PIPER_EXE = os.environ.get("PIPER_EXE", "piper")


Standard-Modelldir; kann via ENV PIPER_MODEL_DIR überschrieben werden.

DEFAULT_MODEL_DIR = os.environ.get(
    "PIPER_MODEL_DIR",
    r"C:\KI\Janus-Projekt\backend\models\piper"
)


Workspace-Cache (entspricht Janus workspace)

WORKSPACE_DIR = Path(os.environ.get(
    "JANUS_WORKSPACE",
    r"C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\workspace"
))
CACHE_DIR = WORKSPACE_DIR / "tts_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


Presets speziell für de_DE-thorsten-high.onnx optimiert

PRESETS = {
    "assistenz": {"length_scale": 0.98, "noise_scale": 0.45, "noise_w": 0.80, "sentence_silence": 0.28},
    "diktat":    {"length_scale": 0.95, "noise_scale": 0.35, "noise_w": 0.70, "sentence_silence": 0.25},
    "narration": {"length_scale": 1.02, "noise_scale": 0.55, "noise_w": 0.90, "sentence_silence": 0.32},
}


Minimalistische deutsche Text-Normalisierung (vorsichtig, nicht aggressiv)

ABBREV_MAP = {
    r"\bz. ?b.\b": "zum Beispiel",
    r"\bca.\b": "circa",
    r"\bu. ?a.\b": "unter anderem",
    r"%": " Prozent",
    r"€": " Euro",
}


class TTSParams(BaseModel):
    length_scale: Optional[float] = None
    noise_scale: Optional[float] = None
    noise_w: Optional[float] = None
    sentence_silence: Optional[float] = None


class TTSRequest(BaseModel):
    text: str
    # voice_id ist der relative Identifier aus /api/tts/voices,
    # voice_path erlaubt direkten Pfad (wird voice_id vorgezogen, wenn beides gesetzt ist).
    voice_id: Optional[str] = None
    voice_path: Optional[str] = None
    preset: Optional[str] = "assistenz"
    params: Optional[TTSParams] = None
    # Optionales Ziel-Format: "wav" (Standard)
    format: Optional[str] = "wav"
    # Ob Caching genutzt werden soll
    use_cache: Optional[bool] = True
    # Sicherheitslimit (Zeichen); wenn None, Standard verwenden
    max_chars: Optional[int] = 4000


class VoiceInfo(BaseModel):
    id: str
    name: str
    path: str
    sample_rate: Optional[int] = None
    language: Optional[str] = None


router = APIRouter(prefix="/api/tts", tags=["tts"])


def _apply_basic_normalization(text: str) -> str:
    norm = text.strip()
    for pat, repl in ABBREV_MAP.items():
        norm = re.sub(pat, repl, norm, flags=re.IGNORECASE)
    # Einfache Datumsersetzung: 15.10. -> 15. Oktober (nicht cases für alle Varianten)
    norm = re.sub(r"\b(\d{1,2}).(\d{1,2}).\b", r"\1. \2.", norm)
    # Mehrfach-Leerzeichen reduzieren
    norm = re.sub(r"\s{2,}", " ", norm)
    return norm


def _resolve_voice_path(voice_id: Optional[str], voice_path: Optional[str]) -> Path:
    if voice_path:
        p = Path(voice_path)
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"Voice path nicht gefunden: {voice_path}")
        return p
    if not voice_id:
        # Fallback: Thorsten als Default
        default_p = Path(DEFAULT_MODEL_DIR) / "de" / "de_DE-thorsten-high.onnx"
        if default_p.exists():
            return default_p
        raise HTTPException(status_code=400, detail="Keine Stimme angegeben und Default nicht gefunden.")
    p = Path(DEFAULT_MODEL_DIR) / voice_id
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"Voice ID nicht gefunden: {voice_id}")
    return p


def _effective_params(preset: Optional[str], params: Optional[TTSParams]) -> Dict[str, float]:
    base = dict(PRESETS.get(preset or "assistenz", PRESETS["assistenz"]))
    if params:
        for k, v in params.dict(exclude_none=True).items():
            base[k] = v
    return base


def _hash_request(text: str, voice_path: Path, eff_params: Dict[str, float]) -> str:
    m = hashlib.sha256()
    m.update(text.encode("utf-8"))
    m.update(str(voice_path.resolve()).encode("utf-8"))
    m.update(json.dumps(eff_params, sort_keys=True).encode("utf-8"))
    return m.hexdigest()


def _binary_available() -> bool:
    exe = shutil.which(PIPER_EXE) if os.path.basename(PIPER_EXE).lower() == PIPER_EXE.lower() else PIPER_EXE
    try:
        return bool(exe) and (shutil.which(PIPER_EXE) is not None or Path(PIPER_EXE).exists())
    except Exception:
        return False


def _scan_model_meta(onnx_path: Path) -> Tuple[Optional[int], Optional[str]]:
    # Versuche optionale JSON-Metadatei zu lesen: .onnx.json
    meta_json = onnx_path.with_suffix(onnx_path.suffix + ".json")
    if meta_json.exists():
        try:
            data = json.loads(meta_json.read_text(encoding="utf-8"))
            sr = data.get("audio", {}).get("sample_rate")
            lang = data.get("language") or data.get("lang") or None
            return sr, lang
        except Exception:
            return None, None
    return None, None


@router.get("/voices", response_model=List[VoiceInfo])
def list_voices() -> List[VoiceInfo]:
    base = Path(DEFAULT_MODEL_DIR)
    if not base.exists():
        raise HTTPException(status_code=500, detail=f"PIPER_MODEL_DIR nicht gefunden: {base}")
    voices: List[VoiceInfo] = []
    for onnx in base.rglob("*.onnx"):
        try:
            vid = str(onnx.relative_to(base)).replace("\", "/")
        except Exception:
            vid = onnx.name
        name = onnx.stem
        sr, lang = _scan_model_meta(onnx)
        voices.append(VoiceInfo(id=vid, name=name, path=str(onnx), sample_rate=sr, language=lang))
    # Sortierung: Sprache/Name
    voices.sort(key=lambda v: (v.language or "", v.name))
    return voices


@router.post("", response_class=Response)
def synthesize(req: TTSRequest):
    if not _binary_available():
        raise HTTPException(status_code=500, detail="Piper-Binary nicht gefunden. Setze PIPER_EXE oder füge piper zum PATH hinzu.")


text = req.text or ""
text = _apply_basic_normalization(text)
if not text:
    raise HTTPException(status_code=400, detail="Leerer Text.")
max_chars = req.max_chars or 4000
if len(text) > max_chars:
    raise HTTPException(status_code=413, detail=f"Text zu lang ({len(text)} Zeichen). Limit: {max_chars}.")

voice_path = _resolve_voice_path(req.voice_id, req.voice_path)
params = _effective_params(req.preset, req.params)

cache_key = _hash_request(text, voice_path, params)
out_wav = CACHE_DIR / f"{cache_key}.wav"

if req.use_cache and out_wav.exists():
    data = out_wav.read_bytes()
    return Response(content=data, media_type="audio/wav")

# Synthesize via Piper (CLI, Text via stdin)
# Sicherheit: temporäre Datei schreiben, dann atomar verschieben
with tempfile.TemporaryDirectory() as td:
    tmp_wav = Path(td) / "out.wav"
    cmd = [
        PIPER_EXE,
        "--model", str(voice_path),
        "--output_file", str(tmp_wav),
        "--length_scale", str(params["length_scale"]),
        "--noise_scale", str(params["noise_scale"]),
        "--noise_w", str(params["noise_w"]),
        "--sentence-silence", str(params["sentence_silence"]),
    ]
    try:
        completed = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
            encoding="utf-8"
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Piper-Timeout (60s).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Piper-Start fehlgeschlagen: {e}")

    if completed.returncode != 0:
        err = (completed.stderr or "").strip()
        raise HTTPException(status_code=500, detail=f"Piper-Fehler (Exit {completed.returncode}): {err}")

    if not tmp_wav.exists() or tmp_wav.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="Piper erzeugte keine Audioausgabe.")

    # Cache schreiben
    try:
        tmp_wav.replace(out_wav)  # atomar auf gleichem Volume
    except Exception:
        out_wav.write_bytes(tmp_wav.read_bytes())

data = out_wav.read_bytes()
return Response(content=data, media_type="audio/wav")

Teil 1b: Router in FastAPI registrieren
Datei: backend/main.py
Ergänze am Anfang die Imports:
from backend.services.tts_service import router as tts_router


Ergänze beim App-Setup:
app.include_router(tts_router)


Teil 1c: Defaults/Umgebung



Standard-Voice (Fallback): C:\KI\Janus-Projekt\backend\models\piper\de\de_DE-thorsten-high.onnx

Setze optional Umgebungsvariablen:

PIPER_EXE="C:\KI\Janus-Projekt\backend\bin\piper.exe" (oder einfach "piper", wenn im PATH)

PIPER_MODEL_DIR="C:\KI\Janus-Projekt\backend\models\piper"

JANUS_WORKSPACE="C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\workspace"




Teil 2: Arbeitsanweisung für den Coding-Agent


Ziel



Backend: TTS-Service per Piper-CLI mit Presets, Caching und Voice-Auflistung bereitstellen.

Frontend: In den Einstellungen zwei Auswahlelemente hinzufügen:

TTS-Engine (Piper CLI, später optional „Piper Library“).

TTS-Stimme (Liste aus /api/tts/voices).



Laufzeit: Synthese per POST /api/tts; Wiedergabe im Frontend aus Blob.


Schritte Backend



Datei anlegen



Erstelle backend/services/tts_service.py mit dem oben bereitgestellten Code.



Router registrieren



Öffne backend/main.py.

Import: from backend.services.tts_service import router as tts_router

Registrierung: app.include_router(tts_router)



Verzeichnisse/ENV



Stelle sicher, dass C:\KI\Janus-Projekt\backend\models\piper existiert und de\de_DE-thorsten-high.onnx enthält.

Setze (lokal beim Start) PIPER_EXE und PIPER_MODEL_DIR falls vom Standard abweichend.



Packaging (PyInstaller)



Falls piper.exe mit ausgeliefert werden soll:

In janus_backend.spec piper.exe zu binaries hinzufügen (oder als externe Abhängigkeit dokumentieren).



Keine zusätzlichen Python-Dependencies notwendig.



Tests (Backend)



GET /api/tts/voices gibt Liste zurück, enthält de_DE-thorsten-high.onnx.

POST /api/tts mit Body:
{
  "text": "Gern. Ich lese das für dich vor.",
  "preset": "assistenz",
  "voice_path": "C:\KI\Janus-Projekt\backend\models\piper\de\de_DE-thorsten-high.onnx"
}
Erwartung: 200, Content-Type audio/wav, Datei im workspace/tts_cache vorhanden.

Fehlerfälle:

Leerer Text -> 400

Piper nicht gefunden -> 500

Timeout erzwingen (extrem langer Text) -> 504



Caching: Zweiter identischer Request ist deutlich schneller (Dateigröße gleich, kein neuer Prozesslauf).


Schritte Frontend



API-Client ergänzen
Datei: frontend/js/api.js (oder bestehender API-Wrapper)



Funktion listTtsVoices():
fetch("/api/tts/voices").then(r => r.json())

Funktion synthesizeTts({ text, preset, voiceId, voicePath }):
fetch("/api/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text, preset, voice_id: voiceId, voice_path: voicePath, use_cache: true })
}).then(async r => {
  if (!r.ok) throw new Error(await r.text());
  return await r.blob();
})



Einstellungen-State
Datei: frontend/js/state/settings.js (oder äquivalente Settings-Verwaltung)



Neue Felder:

ttsEngine: "piper-cli" (Default; später "piper-lib" optional)

ttsVoiceId: string | null

ttsPreset: "assistenz" (Default), weitere: "diktat", "narration"



Persistenz in vorhandener Settings-Struktur sicherstellen.



Einstellungen-UI
Datei: frontend/js/views/settings.js (oder entsprechende Einstellungsseite)



Beim Öffnen: listTtsVoices() aufrufen, Ergebnis in Dropdown "TTS-Stimme" rendern.

Dropdown 1: TTS-Engine

Optionen: "Piper (CLI)" = "piper-cli", "Piper (Library, bald)" = "piper-lib" (disabled)



Dropdown 2: TTS-Stimme

Optionen aus /api/tts/voices; Wert ist voice.id (relativer Pfad innerhalb PIPER_MODEL_DIR).



Dropdown 3: TTS-Preset

assistenz (Empfehlung), diktat, narration



Speichern der Auswahl in settings, sofortige Übernahme.



Audio-Wiedergabe (Beispiel)
Datei: frontend/js/tts_player.js



Funktion playText(text):

Hole settings (engine, voiceId, preset).

Rufe synthesizeTts({ text, preset, voiceId }) auf.

Erzeuge URL.createObjectURL(blob), setze in Audio(), audio.play().



Stop-Funktion für UI-Button implementieren (audio.pause(), currentTime=0).



UI-Validierung



Wenn keine Stimme gewählt ist, zeige Hinweis und wähle Fallback de_DE-thorsten-high.onnx.

Fehler vom Backend (HTTP != 200) sauber anzeigen.



E2E-Test



In Einstellungen „Piper (CLI)“, Stimme „de_DE-thorsten-high“, Preset „assistenz“ wählen.

Testtext aus UI abspielen: „Hallo, ich bin bereit.“

Wechsel auf Preset „diktat“: hörbar schneller, präzisere Diktion.

Wechsel auf „narration“: hörbar wärmer, längere Pausen.


Optionale Erweiterungen (Backlog, nicht blockierend)



Zweiter Driver „piper-lib“: Modell warm laden, geringere Latenz (separater Implementierungspfad in tts_service.py).

Aussprache-Map konfigurierbar machen (Projekt-spezifische Begriffe).

LUFS-Normalisierung als Postprocessing-Flag (z. B. via pyloudnorm), aktuell weggelassen zugunsten einfacher Packaging.

Streaming-API für sehr lange Texte (Chunking).


Akzeptanzkriterien



Die Stimme und das Preset sind aus den Einstellungen heraus wählbar.

/api/tts/voices listet alle verfügbaren .onnx-Modelle unter PIPER_MODEL_DIR.

/api/tts erzeugt zuverlässig WAV-Audio mit Caching (erneute identische Requests sind ohne neuen Synthese-Lauf).

Der Default funktioniert auf deinem Pfad C:\KI\Janus-Projekt\backend\models\piper\de\de_DE-thorsten-high.onnx ohne zusätzliche Konfiguration.
