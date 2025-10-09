Arbeitsanweisung: Piper-TTS Optimierung (Presets, Prosodie, Stimmenauswahl in Einstellungen)

Ziel
- Optimierung der bestehenden Piper-Integration (CLI-Subprozess) ohne Neuaufbau.
- Einführung von drei Qualitäts-Presets (assistenz, diktat, narration).
- Stimmenauswahl in den Einstellungen (Dropdown), gespeist aus dem Piper-Model-Verzeichnis.
- Optional: leichter Text-Normalizer vor der Synthese.

Rahmenbedingungen
- Backend: FastAPI (backend/main.py), Piper via subprocess.run.
- Modelle liegen unter: C:\KI\Janus-Projekt\backend\models\piper (Standard). Fallback/ENV: PIPER_MODEL_DIR.
- Standardstimme: C:\KI\Janus-Projekt\backend\models\piper\de\de_DE-thorsten-high.onnx

Schritt 1: Backend-Änderungen (minimal-invasiv)
1.1 TTS-Implementierung lokalisieren
- Suche im Backend nach dem Aufruf der Piper-CLI (z. B. "subprocess" + "piper").
- Ziel ist die Funktion, die das Kommando baut und ausführt.

1.2 Presets hinzufügen (oberhalb der Synthese-Funktion)
PRESETS = {
    "assistenz": {"length_scale": 0.98, "noise_scale": 0.45, "noise_w": 0.80, "sentence_silence": 0.28},
    "diktat":    {"length_scale": 0.95, "noise_scale": 0.35, "noise_w": 0.70, "sentence_silence": 0.25},
    "narration": {"length_scale": 1.02, "noise_scale": 0.55, "noise_w": 0.90, "sentence_silence": 0.32},
}

1.3 Leichte deutsche Text-Normalisierung (optional, vor dem Aufruf anwenden)
import re

def apply_basic_normalization(text: str) -> str:
    txt = text.strip()
    txt = re.sub(r"\bz\. ?b\.\b", "zum Beispiel", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\bca\.\b", "circa", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\bu\. ?a\.\b", "unter anderem", txt, flags=re.IGNORECASE)
    txt = txt.replace("%", " Prozent").replace("€", " Euro")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt

Anwendung vor Synthese:
text = apply_basic_normalization(text)

1.4 Piper-Parameter aus Preset binden und an CLI übergeben
- Hole Preset-Name und Stimme aus Request/Settings (Details siehe 1.6 und Schritt 2).
- Fallbacks setzen:
  preset_name = settings.ttsPreset or "assistenz"
  p = PRESETS.get(preset_name, PRESETS["assistenz"])
  voice_path = settings.ttsVoicePath or r"C:\\KI\\Janus-Projekt\\backend\\models\\piper\\de\\de_DE-thorsten-high.onnx"

- Kommandozeile sicher mit Parametern bauen (Text via stdin übergeben):
cmd = [
    PIPER_EXE,
    "--model", voice_path,
    "--output_file", str(tmp_wav),
    "--length_scale", str(p["length_scale"]),
    "--noise_scale", str(p["noise_scale"]),
    "--noise_w", str(p["noise_w"]),
    "--sentence-silence", str(p["sentence_silence"]),
]
completed = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=60)
- Exitcode prüfen, Fehler throwen, temporäre Datei atomar verschieben.

1.5 Stimmenliste-Endpoint bereitstellen (für Einstellungen)
- In einem bestehenden Router (z. B. backend/main.py oder eigener tts_router):
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/tts", tags=["tts"])

@router.get("/voices")
def list_voices():
    import os
    base = Path(os.environ.get("PIPER_MODEL_DIR", r"C:\\KI\\Janus-Projekt\\backend\\models\\piper"))
    if not base.exists():
        raise HTTPException(status_code=500, detail=f"PIPER_MODEL_DIR nicht gefunden: {base}")
    voices = []
    for onnx in base.rglob("*.onnx"):
        try:
            vid = str(onnx.relative_to(base)).replace("\\", "/")
        except Exception:
            vid = onnx.name
        voices.append({"id": vid, "name": onnx.stem, "path": str(onnx)})
    voices.sort(key=lambda v: v["name"])  # einfache Sortierung
    return voices

- Router registrieren (falls noch nicht): app.include_router(router)

1.6 Request-Contract der bestehenden TTS-Route minimal erweitern
- Erlaube optionale Felder: preset, voice_id, voice_path.
- Auflösung:
  - Wenn voice_path gesetzt: nutze diesen.
  - Sonst, wenn voice_id gesetzt: path = PIPER_MODEL_DIR / voice_id.
  - Sonst Fallback: de_DE-thorsten-high.onnx
- Preset auflösen: p = PRESETS.get(preset or "assistenz", PRESETS["assistenz"])

1.7 Optional: Caching beibehalten oder ergänzen (falls nicht vorhanden)
- Key = sha256(text + voice_path + preset)
- Ausgabedatei unter workspace/tts_cache/<key>.wav ablegen; bei Treffer nicht neu synthesen.

Schritt 2: Frontend-Änderungen (Einstellungen)
2.1 Settings-State erweitern
- Neue Felder: settings.ttsPreset (Default: "assistenz"), settings.ttsVoiceId (Default: Pfad/ID der Thorsten-Stimme).
- Persistenz wie bestehende Settings.

2.2 API-Hilfsfunktionen
- listTtsVoices(): GET /api/tts/voices -> Array von {id, name, path}.
- synthesizeTts(payload): POST /api/tts mit { text, preset: settings.ttsPreset, voice_id: settings.ttsVoiceId }.

2.3 Einstellungen-UI
- Dropdown "TTS-Stimme": mit listTtsVoices() befüllen; Wert = voice.id; Label = name.
- Dropdown "TTS-Preset": Optionen [assistenz, diktat, narration].
- Beim Speichern: Werte in settings persistieren.

2.4 TTS-Aufruf anpassen
- Beim Abspielen text -> synthesizeTts({ text, preset: settings.ttsPreset, voice_id: settings.ttsVoiceId }).

2.5 Schnelltest-Button
- Neben den Dropdowns Button "Stimmtest"; Beispieltext senden: "Hallo, das ist ein kurzer Test." und Audio direkt abspielen.

Schritt 3: Qualitätssicherung
- GET /api/tts/voices liefert mind. Thorsten-Modell.
- Drei Presets hörbar unterscheidbar:
  - assistenz: ruhig, natürliche Pausen.
  - diktat: schneller, klare Artikulation.
  - narration: etwas wärmer, längere Pausen.
- Bei identischem Text + Stimme + Preset (falls Cache aktiv): Wiederholung schneller, gleiche WAV-Größe.
- Fehlerpfade: Leerer Text -> 400; fehlender Piper-Binary -> 500 (klarer Fehlertext).

Schritt 4: Akzeptanzkriterien
- Stimmen- und Preset-Auswahl sind in den Einstellungen verfügbar und persistent.
- Die Auswahl wirkt sich direkt auf neue TTS-Ausgaben aus.
- Keine Änderung am grundsätzlichen Start von Piper (weiterhin CLI-Subprozess).

Schritt 5: Rollback
- Die Änderung ist rückbaubar, da nur zusätzliche Parameter/Endpoints ergänzt wurden.
- Deaktivierung möglich, indem preset auf "assistenz" fixiert und die UI-Felder ausgeblendet werden.

Parameter-Referenz (für schnelle Anpassungen)
- assistenz: length_scale 0.98, noise_scale 0.45, noise_w 0.80, sentence_silence 0.28
- diktat: length_scale 0.95, noise_scale 0.35, noise_w 0.70, sentence_silence 0.25
- narration: length_scale 1.02, noise_scale 0.55, noise_w 0.90, sentence_silence 0.32

Hinweise
- Satzzeichen bewusst im Text nutzen (Kommas, Punkte, Ellipsen) für bessere Prosodie.
- Lange Sätze vor dem Senden ggf. in Sinnphrasen splitten.
- Falls Packaging: PIPER_EXE via ENV setzen oder im System-PATH belassen.