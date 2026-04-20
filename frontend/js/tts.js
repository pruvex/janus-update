import { API_BASE_URL } from "./config.js";
import { paneId } from "./window-state.js";

let ttsEnabled = false;
let ttsVoice = null;
let ttsSpeed = 1.0;
export let ttsPreset = null; // NEU
let currentAudio = null;

/**
 * Load available TTS voices from the backend
 */
export async function loadTTSVoices(lang = null) {
  try {
    const url = lang
      ? `${API_BASE_URL}/api/tts/voices?lang=${encodeURIComponent(lang)}`
      : `${API_BASE_URL}/api/tts/voices`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to load voices");
    const data = await response.json();
    return data.voices;
  } catch (error) {
    console.error("Error loading TTS voices:", error);
    return [];
  }
}

/**
 * Synthesize speech from text
 */
export async function synthesizeSpeech({
  text,
  lang,
  voice_id,
  speed = 1.0,
  format = "mp3",
  provider = null,
  preset = null,
  llm_provider = null,
}) {
  try {
    const params = new URLSearchParams({
      text,
      lang,
      speed: String(speed),
      fmt: format,
    });

    if (voice_id) params.append("voice_id", voice_id);
    if (provider) params.append("provider", provider);
    if (preset) params.append("preset", preset);
    if (llm_provider) params.append("llm_provider", llm_provider); // NEU: llm_provider hinzufügen

    const response = await fetch(`${API_BASE_URL}/api/tts/synthesize?${params.toString()}`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "TTS synthesis failed");
    }

    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error("TTS synthesis error:", error);
    throw error;
  }
}

/**
 * Play text as speech
 */
export async function speakText(text, lang = "de", llm_provider = null) {
  if (!ttsEnabled) return;

  // Stop any currently playing audio
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  try {
    const audioUrl = await synthesizeSpeech({
      text,
      lang,
      voice_id: ttsVoice,
      speed: ttsSpeed,
      format: "mp3",
      preset: ttsPreset,
      llm_provider: llm_provider, // NEU: llm_provider übergeben
    });

    currentAudio = new Audio(audioUrl);
    currentAudio.play();

    currentAudio.addEventListener("ended", () => {
      URL.revokeObjectURL(audioUrl);
      currentAudio = null;
    });
  } catch (error) {
    console.error("Error speaking text:", error);
  }
}

/**
 * Enable/disable TTS
 */
export function setTTSEnabled(enabled) {
  ttsEnabled = enabled;
  localStorage.setItem("tts_enabled", enabled ? "true" : "false");

  // Update button state
  const ttsBtn = document.getElementById(paneId("tts-toggle-btn"));
  if (ttsBtn) {
    ttsBtn.classList.toggle("active", enabled);
    ttsBtn.title = enabled ? "TTS aktiviert" : "TTS deaktiviert";
  }
}

/**
 * Get TTS enabled state
 */
export function isTTSEnabled() {
  return ttsEnabled;
}

/**
 * Set TTS voice
 */
export function setTTSVoice(voice) {
  ttsVoice = voice;
  localStorage.setItem("tts_voice", voice);
}

/**
 * Set TTS speed
 */
export function setTTSSpeed(speed) {
  ttsSpeed = speed;
  localStorage.setItem("tts_speed", String(speed));
}

/**
 * Initialize TTS system
 */
export async function initTTS() {
  // Load saved settings from backend
  try {
    const response = await fetch(`${API_BASE_URL}/api/tts/settings`);
    const settings = await response.json();

    ttsVoice = settings.voice || null;
    ttsSpeed = settings.speed || 1.0;
    ttsPreset = settings.preset || "assistenz";
  } catch (error) {
    console.error("Error loading TTS settings for init:", error);
    // Fallback to localStorage if backend fails
    ttsVoice = localStorage.getItem("tts_voice");
    ttsSpeed = parseFloat(localStorage.getItem("tts_speed")) || 1.0;
    ttsPreset = localStorage.getItem("tts_preset") || "assistenz";
  }

  // Load enabled state from localStorage (this is a local UI preference)
  const savedEnabled = localStorage.getItem("tts_enabled") === "true";
  ttsEnabled = savedEnabled;

  // Set up toggle button
  const ttsBtn = document.getElementById(paneId("tts-toggle-btn"));
  if (ttsBtn) {
    ttsBtn.classList.toggle("active", ttsEnabled);
    ttsBtn.addEventListener("click", () => {
      setTTSEnabled(!ttsEnabled);
    });
  }
}
