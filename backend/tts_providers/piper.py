import os
import re
import subprocess
import shutil
import io
import logging
from typing import Generator, Optional, List, Dict
from pydub import AudioSegment
from num2words import num2words

from backend.tts_providers.base import TTSProviderBase
from backend.utils.paths import resource_path

logger = logging.getLogger("janus_backend")

# Piper binary candidates
PIPER_BINARY_CANDIDATES = [
    resource_path("backend/bin/piper.exe"),  # Windows
    resource_path("backend/bin/piper"),      # Linux/Mac
]

# Available Piper models
PIPER_MODELS = {
    "de_DE-thorsten-high": {
        "model": resource_path("backend/models/piper/de/de_DE-thorsten-high.onnx"),
        "json": resource_path("backend/models/piper/de/de_DE-thorsten-high.onnx.json")
    },
    "de_DE-thorsten-medium": {
        "model": resource_path("backend/models/piper/de/de_DE-thorsten-medium.onnx"),
        "json": resource_path("backend/models/piper/de/de_DE-thorsten-medium.onnx.json")
    },
    "de_DE-eva_k-x_low": {
        "model": resource_path("backend/models/piper/de/de_DE-eva_k-x_low.onnx"),
        "json": resource_path("backend/models/piper/de/de_DE-eva_k-x_low.onnx.json")
    },
    "de_DE-eva_k-hifi": {
        "model": resource_path("backend/models/piper/de/de_DE-eva_k-hifi.onnx"),
        "json": resource_path("backend/models/piper/de/de_DE-eva_k-hifi.onnx.json")
    },
    "en-US-high": {
        "model": resource_path("backend/models/piper/en/en_US-high.onnx"),
        "json": resource_path("backend/models/piper/en/en_US-high.onnx.json")
    },
}

PRESETS = {
    "assistenz": {"length_scale": 0.98, "noise_scale": 0.45, "noise_w": 0.80, "sentence_silence": 0.28},
    "diktat":    {"length_scale": 0.95, "noise_scale": 0.35, "noise_w": 0.70, "sentence_silence": 0.25},
    "narration": {"length_scale": 1.02, "noise_scale": 0.55, "noise_w": 0.90, "sentence_silence": 0.32},
}

def apply_basic_normalization(text: str) -> str:
    txt = text.strip()
    txt = re.sub(r"\bz\. ?b\.\b", "zum Beispiel", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\bca\.\b", "circa", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\bu\. ?a\.\b", "unter anderem", txt, flags=re.IGNORECASE)
    txt = re.sub(r"(\bden\s+)(\d{1,2})\.", lambda m: f"{m.group(1)}{num2words(int(m.group(2)), to='ordinal', lang='de') + ('n' if num2words(int(m.group(2)), to='ordinal', lang='de').endswith('e') else '')}", txt, flags=re.IGNORECASE)
    txt = txt.replace("%", " Prozent").replace("€", " Euro")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt



def _find_piper_binary() -> Optional[str]:
    """Find Piper binary in bundled paths or system PATH."""
    for cand in PIPER_BINARY_CANDIDATES:
        if os.path.exists(cand):
            logger.info(f"Found Piper binary at: {cand}")
            return cand
    
    # Fallback: check system PATH
    bin_name = "piper.exe" if os.name == "nt" else "piper"
    p = shutil.which(bin_name)
    if p:
        logger.info(f"Found Piper binary in PATH: {p}")
        return p
    
    logger.warning("Piper binary not found")
    return None


class PiperTTS(TTSProviderBase):
    """Piper TTS Provider - Fast local ONNX-based TTS."""
    name = "piper"

    def __init__(self):
        self.binary = _find_piper_binary()

    def is_available(self) -> bool:
        """Check if Piper is available."""
        return self.binary is not None

    def list_voices(self) -> List[Dict]:
        """List available Piper voices."""
        voices = []
        for voice_id, config in PIPER_MODELS.items():
            # Extract language from voice_id (e.g., de_DE-thorsten-high -> de)
            lang = voice_id.split('_')[0].lower()
            voices.append({
                "id": voice_id,
                "name": voice_id.replace('_', ' ').replace('-', ' ').title(), # Simple name generation
                "lang": lang,
                "path": config["model"]
            })
        return voices

    def supports_streaming(self, fmt: str) -> bool:
        # Piper can stream WAV output
        return fmt.lower() in ("wav", "mp3", "ogg")

    def synthesize(self, text: str, voice: str, lang: str, speed: float, fmt: str, preset_name: Optional[str] = None) -> bytes:
        """Synthesize speech using Piper."""
        if not self.is_available():
            raise RuntimeError("Piper binary not available")
        
        # Remove 'piper_' prefix if present
        voice_id = voice.replace('piper_', '', 1) if voice.startswith('piper_') else voice
        wav_bytes = self._run_piper(text=text, voice=voice_id, speed=speed, preset_name=preset_name)
        
        if fmt.lower() == "wav":
            return wav_bytes
        
        # Re-encode to requested format
        seg = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
        out = io.BytesIO()
        if fmt.lower() == "mp3":
            seg.export(out, format="mp3")
        else:
            seg.export(out, format="ogg")
        return out.getvalue()

    def synthesize_stream(self, text: str, voice: str, lang: str, speed: float, fmt: str, preset_name: Optional[str] = None):
        """Stream audio synthesis from Piper."""
        if not self.is_available():
            raise RuntimeError("Piper binary not available")
        
        def gen():
            # Remove 'piper_' prefix if present
            voice_id = voice.replace('piper_', '', 1) if voice.startswith('piper_') else voice
            wav_stream = self._run_piper_stream(text=text, voice=voice_id, speed=speed, preset_name=preset_name)
            for chunk in wav_stream:
                yield chunk
        return gen()

    def _run_piper(self, text: str, voice: str, speed: float, preset_name: Optional[str] = None) -> bytes:
        """Run Piper binary and return WAV bytes."""
        model = PIPER_MODELS.get(voice)
        if not model:
            raise ValueError(f"Unknown Piper voice: {voice}")
        
        # Normalize paths for Windows
        model_path = os.path.normpath(model["model"])
        json_path = os.path.normpath(model["json"])
        binary_path = os.path.normpath(self.binary)
        
        logger.info(f"Checking Piper model at: {model_path}")
        
        if not os.path.exists(model_path):
            logger.error(f"Piper model not found at: {model_path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            raise FileNotFoundError(f"Piper model not found: {model_path}")
        
        if not os.path.exists(binary_path):
            logger.error(f"Piper binary not found at: {binary_path}")
            raise FileNotFoundError(f"Piper binary not found: {binary_path}")
        
        # Apply basic normalization
        text = apply_basic_normalization(text)

        # Get preset parameters
        p = PRESETS.get(preset_name, PRESETS["assistenz"])

        args = [
            binary_path,
            "-m", model_path,
            "-f", "wav",
            "--length-scale", str(p["length_scale"]),
            "--noise-scale", str(p["noise_scale"]),
            "--noise-w", str(p["noise_w"]),
            "--sentence-silence", str(p["sentence_silence"]),
        ]
        
        # Add speaker if multi-speaker model
        if "speaker" in str(json_path):
            args += ["--speaker", "0"]
        
        if os.path.exists(json_path):
            args += ["-c", json_path]
        
        logger.info(f"Running Piper with args: {args}")
        logger.debug(f"Text to synthesize (length {len(text)}): {text[:100]}...")
        
        # Use a temporary file for output to avoid stdout buffering issues
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_output:
            output_file = tmp_output.name
        
        # Add output file to args instead of using stdout
        args_with_output = args + ["--output_file", output_file]
        
        try:
            proc = subprocess.Popen(
                args_with_output,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(binary_path)
            )
            stdout_data, err = proc.communicate(input=text.encode("utf-8"), timeout=120)
            
            # Read the generated file
            if not os.path.exists(output_file):
                raise RuntimeError(f"Piper did not create output file: {output_file}")
            
            with open(output_file, "rb") as f:
                out = f.read()
            
            # Clean up temp file
            try:
                os.unlink(output_file)
            except:
                pass
            
            # Always log stderr for debugging
            if err:
                err_msg = err.decode('utf-8', errors='ignore')
                logger.debug(f"Piper stderr: {err_msg}")
            
            if proc.returncode != 0:
                error_msg = err.decode('utf-8', errors='ignore') if err else "No error message"
                logger.error(f"Piper error (code {proc.returncode}): {error_msg}")
                raise RuntimeError(f"Piper synthesis failed: {error_msg}")
            
            logger.info(f"Piper synthesis successful, output size: {len(out)} bytes")
            
            # Validate output is not empty or too small
            if len(out) < 100:
                logger.error(f"Piper output suspiciously small ({len(out)} bytes). This is likely an error.")
                logger.error(f"Output hex: {out.hex()}")
                raise RuntimeError(f"Piper produced invalid output (only {len(out)} bytes)")
            return out
        except subprocess.TimeoutExpired:
            proc.kill()
            raise RuntimeError("Piper synthesis timed out")
        except FileNotFoundError as e:
            logger.error(f"Piper binary or dependencies not found: {e}")
            logger.error(f"Binary path: {binary_path}")
            logger.error(f"Make sure all DLLs are in backend/bin/")
            raise
        except Exception as e:
            logger.error(f"Piper execution failed: {e}")
            raise

    def _run_piper_stream(self, text: str, voice: str, speed: float, preset_name: Optional[str] = None):
        """Run Piper and stream output."""
        model = PIPER_MODELS.get(voice)
        if not model:
            raise ValueError(f"Unknown Piper voice: {voice}")
        
        # Apply basic normalization
        text = apply_basic_normalization(text)

        # Get preset parameters
        p = PRESETS.get(preset_name, PRESETS["assistenz"])

        args = [
            self.binary,
            "-m", model["model"],
            "-f", "wav",
            "--length-scale", str(p["length_scale"]),
            "--noise-scale", str(p["noise_scale"]),
            "--noise-w", str(p["noise_w"]),
            "--sentence-silence", str(p["sentence_silence"]),
        ]
        
        if os.path.exists(model["json"]):
            args += ["-c", model["json"]]
        
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        
        proc.stdin.write(text.encode("utf-8"))
        proc.stdin.close()
        
        def stream():
            try:
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
                proc.wait(timeout=10)
                if proc.returncode != 0:
                    err = proc.stderr.read().decode("utf-8", errors="ignore")
                    raise RuntimeError(f"Piper error: {err}")
            finally:
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()
        
        return stream()
